"""Turn GCOV subsets into web-ready images + stats.

For each site/date:
  - reproject HH, HV (linear power, sigma0/gamma0 as delivered) to EPSG:4326 on a common grid
  - 5x5 boxcar speckle filter, convert to dB
  - RGB composite: R=HH, G=HV, B=HH/HV (fixed stretch so dates are comparable)
  - change layer: HH dB difference vs. the first date (diverging colours, transparent where |d| < 2 dB)
  - mean HH / HV dB inside the study area -> stats for the trend chart
Writes web/data/<site>/<date>_{rgb,hh,hv,chg}.webp and web/data/sites.json

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
RES = 0.00025  # degrees (~25 m) for web images
HH_RANGE = (-24.0, 2.0)
HV_RANGE = (-30.0, -6.0)
RATIO_RANGE = (0.0, 18.0)
CHG_MIN, CHG_MAX = 2.0, 10.0


# product maturity and processing CRID come from the granule list itself, not from the date
_MAN = {r[0]: (r[1], r[3].split("_")[-5]) for r in json.load(open(ROOT / "data" / "search_result.json"))["saemangeum"]["133/70/DESCENDING"]}
_TAG = {"BETA": "BETA", "PROVISIONAL": "PROVISIONAL", "VAL": "VALIDATED", "VALIDATED": "VALIDATED"}


def collection_of(date):
    return _TAG[_MAN[date][0]]


def crid_of(date):
    return _MAN[date][1]


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
    Image.fromarray(arr, "RGBA").save(path, "WEBP", quality=82, method=4)


def render_one(site, date, ref_date):
    cfg = SITES[site]; d = WEB / site
    ref = to_db(load_on_grid(SUB / f"{site}_{ref_date}_HH.tif", cfg["bbox"]))
    hh = load_on_grid(SUB / f"{site}_{date}_HH.tif", cfg["bbox"])
    hvp = SUB / f"{site}_{date}_HV.tif"
    hv = load_on_grid(hvp, cfg["bbox"]) if hvp.exists() else np.full_like(hh, np.nan)
    hhdb, hvdb = to_db(hh), to_db(hv)
    valid = np.isfinite(hhdb)
    alpha = (valid * 255).astype("uint8")
    r = stretch(hhdb, *HH_RANGE); g = stretch(hvdb, *HV_RANGE); b = stretch(hhdb - hvdb, *RATIO_RANGE)
    rgb = np.dstack([np.nan_to_num(x) * 255 for x in (r, g, b)]).astype("uint8")
    save_rgba(np.dstack([rgb, alpha]), d / f"{date}_rgb.webp")
    for name, arr, rng in (("hh", hhdb, HH_RANGE), ("hv", hvdb, HV_RANGE)):
        gimg = (np.nan_to_num(stretch(arr, *rng)) * 255).astype("uint8")
        save_rgba(np.dstack([gimg, gimg, gimg, (np.isfinite(arr) * 255).astype("uint8")]), d / f"{date}_{name}.webp")
    diff = hhdb - ref
    mag = np.clip((np.abs(diff) - CHG_MIN) / (CHG_MAX - CHG_MIN), 0, 1)
    up = diff > 0
    chg = np.zeros(diff.shape + (4,), dtype="uint8")
    chg[..., 0] = np.where(up, 255, 77); chg[..., 1] = np.where(up, 159, 163); chg[..., 2] = np.where(up, 67, 255)
    chg[..., 3] = (np.nan_to_num(mag) * 230).astype("uint8")
    beta = collection_of(date) == "BETA"
    if beta:  # uncalibrated vs calibrated differences are not meaningful -> nothing drawn
        chg[..., 3] = 0
    save_rgba(chg, d / f"{date}_chg.webp")
    frac_up = None if beta or not valid.any() else float(np.nanmean((diff > CHG_MIN)[valid]))
    frac_dn = None if beta or not valid.any() else float(np.nanmean((diff < -CHG_MIN)[valid]))
    print(site, date, "ok", flush=True)
    return {"date": date, "collection": collection_of(date), "crid": crid_of(date),
            "hh_db": float(np.nanmedian(hhdb)), "hv_db": float(np.nanmedian(hvdb)) if np.isfinite(hvdb).any() else None,
            "frac_brighter": frac_up, "frac_darker": frac_dn}


# Persistent HH-brightening candidates (calibrated PROVISIONAL/VALIDATED dates only).
# A pixel is a candidate when HH is <= EARLY_MAX dB on ALL three early-summer dates and >= LATE_MIN dB on ALL three
# autumn dates. Candidates are grouped into patches (8-connected after a 1-pixel dilation, >= MIN_PX original pixels).
# This flags radar brightening that persisted; it does NOT prove construction (see the method page).
NEW_EARLY = ["2026-06-23", "2026-07-05", "2026-07-17"]
NEW_LATE = ["2026-10-09", "2026-10-21", "2026-11-02"]
NEW_EARLY_MAX, NEW_LATE_MIN, MIN_PX = -8.0, -3.0, 4
CROP = 48  # half-size of evidence crops in pixels (~1.1 x 1.3 km box)


def render_new(site, all_dates):
    from scipy.ndimage import binary_dilation, label, find_objects
    cfg = SITES[site]; bb = cfg["bbox"]; d = WEB / site; (d / "spots").mkdir(exist_ok=True)
    hh = {dt: to_db(load_on_grid(SUB / f"{site}_{dt}_HH.tif", bb)) for dt in all_dates}
    E = np.stack([hh[x] for x in NEW_EARLY]); La = np.stack([hh[x] for x in NEW_LATE])
    finite = np.isfinite(E).all(0) & np.isfinite(La).all(0)  # all six observations must exist
    with np.errstate(invalid="ignore"):
        passed = finite & (La.min(0) >= NEW_LATE_MIN) & (E.max(0) <= NEW_EARLY_MAX)
    new = passed.copy()
    lab, n = label(binary_dilation(new, iterations=1), structure=np.ones((3, 3)))
    lat0 = (bb[1] + bb[3]) / 2
    dy_m, dx_m = RES * 111320, RES * 111320 * np.cos(np.radians(lat0))
    spots = []
    for k, sl in enumerate(find_objects(lab), start=1):
        m = (lab[sl] == k) & new[sl]
        if m.sum() < MIN_PX:
            continue
        ys, xs = np.nonzero(m); y0, x0 = sl[0].start, sl[1].start
        cy, cx = int(round(y0 + ys.mean())), int(round(x0 + xs.mean()))
        lat = bb[3] - (cy + 0.5) * RES; lon = bb[0] + (cx + 0.5) * RES
        series = [round(float(np.nanmedian(hh[dt][sl][m])), 2) for dt in all_dates]
        spots.append({"lat": round(lat, 5), "lon": round(lon, 5), "px": int(m.sum()),
                      "ha": round(float(m.sum()) * dx_m * dy_m / 1e4, 2), "series": series, "_c": (cy, cx),
                      "_mask": (slice(None), slice(None))})
        mm = np.zeros_like(new); mm[sl] = m; spots[-1]["_mask"] = mm
    spots.sort(key=lambda q: -q["px"])
    kept = np.zeros_like(new)
    for q in spots:
        q["_m2"] = q.pop("_mask"); kept[q["_m2"]] = True
    new = kept  # map and totals show only retained patches
    H, W = new.shape
    ids = np.zeros(new.shape, dtype="int16")
    for i, q in enumerate(spots, start=1):
        q["id"] = i; cy, cx = q.pop("_c")
        ids[q.pop("_m2")] = i
        if i <= 12:  # evidence crops: first calibrated date vs latest date, same RGB stretch as the map
            ya, yb, xa, xb = max(0, cy - CROP), min(H, cy + CROP), max(0, cx - CROP), min(W, cx + CROP)
            for tag, dt in (("before", NEW_EARLY[0]), ("after", NEW_LATE[-1])):
                im = Image.open(d / f"{dt}_rgb.webp").convert("RGB").crop((xa, ya, xb, yb)).resize(((xb - xa) * 2, (yb - ya) * 2), Image.NEAREST)
                im.save(d / "spots" / f"{i}_{tag}.webp", "WEBP", quality=85)
            q["crop"] = True
    show = binary_dilation(new, iterations=2)
    img = np.zeros(new.shape + (4,), dtype="uint8"); img[show] = [255, 159, 67, 235]
    save_rgba(img, d / "new.webp")
    gj = {"type": "FeatureCollection", "properties": {"site": site, "rule": f"HH<= {NEW_EARLY_MAX} dB on {NEW_EARLY} and HH>= {NEW_LATE_MIN} dB on {NEW_LATE}", "pixel_spacing_deg": RES, "dates": all_dates},
          "features": [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [q["lon"], q["lat"]]},
                        "properties": {"id": q["id"], "pixels": q["px"], "area_ha": q["ha"], "hh_median_db": q["series"]}} for q in spots]}
    json.dump(gj, open(WEB / f"{site}_candidates.geojson", "w"), indent=1)
    # for the optical cross-check (03_optical_hls.py): patch ids, plus a control set = pixels that were just as dark
    # in summer (same early rule, six finite dates) but did NOT pass, kept >= 3 px away from any candidate
    with np.errstate(invalid="ignore"):
        control = finite & (E.max(0) <= NEW_EARLY_MAX) & ~binary_dilation(passed, iterations=3)
    (ROOT / "data" / "derived").mkdir(exist_ok=True)
    np.savez_compressed(ROOT / "data" / "derived" / f"{site}_patches.npz", ids=ids, control=control)
    print(site, "candidate px", int(new.sum()), "patches", len(spots), flush=True)
    return {"new_ha": round(float(new.sum()) * dx_m * dy_m / 1e4, 1), "new_px_passed": int(passed.sum()), "new_px_kept": int(new.sum()),
            "new_spot_count": len(spots), "new_spots": spots[:12],
            "new_early": NEW_EARLY, "new_late": NEW_LATE}


def main():
    from concurrent.futures import ProcessPoolExecutor
    files = sorted(SUB.glob("*_HH.tif"))
    index = {}
    for f in files:
        m = re.match(r"(\w+?)_(\d{4}-\d{2}-\d{2})_HH\.tif", f.name)
        if m:
            index.setdefault(m.group(1), []).append(m.group(2))
    out = {"generated_by": "scripts/02_render.py", "sites": []}
    jobs = {}
    with ProcessPoolExecutor(max_workers=6) as ex:
        for site, dates in index.items():
            dates = sorted(set(dates)); (WEB / site).mkdir(exist_ok=True)
            # change reference = first calibrated (PROVISIONAL or later) date; BETA data is uncalibrated
            ref_date = next((x for x in dates if collection_of(x) != "BETA"), dates[0])
            jobs[site] = (ref_date, [ex.submit(render_one, site, dt, ref_date) for dt in dates], None)
        for site in jobs:
            jobs[site] = (jobs[site][0], [f.result() for f in jobs[site][1]], ex.submit(render_new, site, sorted(set(index[site]))))
        for site, (ref_date, futs, fnew) in jobs.items():
            cfg = SITES[site]; w, s, e, n = cfg["bbox"]
            out["sites"].append({"id": site, "name": cfg["name"], "bounds": [[s, w], [n, e]], "ref_date": ref_date,
                                 "dates": futs, **fnew.result()})
    json.dump(out, open(WEB / "sites.json", "w"), indent=1)


if __name__ == "__main__":
    main()
