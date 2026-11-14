"""Turn GCOV subsets into web-ready images + stats.

For each site/date:
  - reproject HH, HV (linear power, sigma0/gamma0 as delivered) to EPSG:4326 on a common grid
  - 5x5 boxcar speckle filter, convert to dB
  - RGB composite: R=HH, G=HV, B=HH/HV (fixed stretch so dates are comparable)
  - change layer: HH dB difference vs. the first date (diverging colours, transparent where |d| < 2 dB)
  - mean HH / HV dB inside the study area -> stats for the trend chart
Writes web/data/<site>/<date>_{rgb,hh,hv,chg}.png and web/data/sites.json

SI note: drafted with SI assistance (Claude) and reviewed by the team.
"""
import json, re
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
from scipy.ndimage import uniform_filter
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "data" / "subsets"
WEB = ROOT / "web" / "data"
WEB.mkdir(parents=True, exist_ok=True)

SITES = {
    "saemangeum": {"name": "Saemangeum, Korea", "bbox": (126.42, 35.68, 126.80, 35.99)},
    "yongin": {"name": "Yongin, Korea", "bbox": (127.12, 37.04, 127.40, 37.22)},
}
RES = 0.0004  # degrees (~40 m) for web images
HH_RANGE = (-24.0, 2.0)
HV_RANGE = (-32.0, -8.0)
RATIO_RANGE = (0.0, 18.0)
CHG_MIN, CHG_MAX = 2.0, 10.0


def collection_of(date):
    if date < "2026-06-01":
        return "BETA"
    if date < "2026-10-21":
        return "PROVISIONAL"
    return "VALIDATED"


def load_on_grid(path, bbox):
    w, s, e, n = bbox
    width = int(round((e - w) / RES)); height = int(round((n - s) / RES))
    dst_tr = rasterio.transform.from_origin(w, n, RES, RES)
    out = np.full((height, width), np.nan, dtype="float32")
    with rasterio.open(path) as src:
        a = src.read(1).astype("float32")
        a[a <= 0] = np.nan
        # speckle filter in native geometry (ignore NaNs)
        m = np.isfinite(a)
        num = uniform_filter(np.where(m, a, 0), 5); den = uniform_filter(m.astype("float32"), 5)
        a = np.where(den > 0.2, num / np.maximum(den, 1e-6), np.nan).astype("float32")
        reproject(a, out, src_transform=src.transform, src_crs=src.crs, dst_transform=dst_tr,
                  dst_crs="EPSG:4326", resampling=Resampling.average, src_nodata=np.nan, dst_nodata=np.nan)
    return out


def to_db(a):
    with np.errstate(divide="ignore", invalid="ignore"):
        return 10 * np.log10(a)


def stretch(a, lo, hi):
    return np.clip((a - lo) / (hi - lo), 0, 1)


def save_rgba(arr, path):
    Image.fromarray(arr, "RGBA").save(path, optimize=True)


def main():
    files = sorted(SUB.glob("*_HH.tif"))
    index = {}
    for f in files:
        m = re.match(r"(\w+?)_(\d{4}-\d{2}-\d{2})_HH\.tif", f.name)
        if m:
            index.setdefault(m.group(1), []).append(m.group(2))
    out = {"generated_by": "scripts/02_render.py", "sites": []}
    for site, dates in index.items():
        cfg = SITES[site]; dates = sorted(set(dates))
        d = WEB / site; d.mkdir(exist_ok=True)
        ref = None; recs = []
        for date in dates:
            hh = load_on_grid(SUB / f"{site}_{date}_HH.tif", cfg["bbox"])
            hvp = SUB / f"{site}_{date}_HV.tif"
            hv = load_on_grid(hvp, cfg["bbox"]) if hvp.exists() else np.full_like(hh, np.nan)
            hhdb, hvdb = to_db(hh), to_db(hv)
            valid = np.isfinite(hhdb)
            alpha = (valid * 255).astype("uint8")
            r = stretch(hhdb, *HH_RANGE); g = stretch(hvdb, *HV_RANGE); b = stretch(hhdb - hvdb, *RATIO_RANGE)
            rgb = np.dstack([np.nan_to_num(x) * 255 for x in (r, g, b)]).astype("uint8")
            save_rgba(np.dstack([rgb, alpha]), d / f"{date}_rgb.png")
            for name, arr, rng in (("hh", hhdb, HH_RANGE), ("hv", hvdb, HV_RANGE)):
                gimg = (np.nan_to_num(stretch(arr, *rng)) * 255).astype("uint8")
                save_rgba(np.dstack([gimg, gimg, gimg, (np.isfinite(arr) * 255).astype("uint8")]), d / f"{date}_{name}.png")
            if ref is None:
                ref = hhdb
            diff = hhdb - ref
            mag = np.clip((np.abs(diff) - CHG_MIN) / (CHG_MAX - CHG_MIN), 0, 1)
            up = diff > 0
            chg = np.zeros(diff.shape + (4,), dtype="uint8")
            chg[..., 0] = np.where(up, 255, 77); chg[..., 1] = np.where(up, 159, 163); chg[..., 2] = np.where(up, 67, 255)
            chg[..., 3] = (np.nan_to_num(mag) * 230).astype("uint8")
            save_rgba(chg, d / f"{date}_chg.png")
            frac_up = float(np.nanmean((diff > CHG_MIN)[valid])) if valid.any() else None
            frac_dn = float(np.nanmean((diff < -CHG_MIN)[valid])) if valid.any() else None
            recs.append({"date": date, "collection": collection_of(date),
                         "hh_db": float(np.nanmedian(hhdb)), "hv_db": float(np.nanmedian(hvdb)) if np.isfinite(hvdb).any() else None,
                         "frac_brighter": frac_up, "frac_darker": frac_dn})
            print(site, date, "ok")
        w, s, e, n = cfg["bbox"]
        out["sites"].append({"id": site, "name": cfg["name"], "bounds": [[s, w], [n, e]], "dates": recs})
    json.dump(out, open(WEB / "sites.json", "w"), indent=1)


if __name__ == "__main__":
    main()
