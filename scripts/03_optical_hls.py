"""Independent optical cross-check with NASA HLS (Harmonized Landsat and Sentinel-2, v2.0).

For each site we build two clear-sky median composites on the same 0.00025 deg grid as the radar images:
  summer = 2026-06-01 .. 2026-07-31 (around the radar's early dates Jun 23 - Jul 17)
  autumn = 2026-10-01 .. 2026-11-10 (around the radar's late dates Oct 9 - Nov 2)
Only pixels flagged clear by HLS Fmask (no cloud, adjacent cloud, shadow or snow) are used.

Outputs (web/data):
  <site>/hls_summer.webp, <site>/hls_autumn.webp   true-colour composites (map layer + evidence crops)
  <site>/spots/<id>_hls_before.webp / _hls_after.webp
  optical.json  per-patch NDVI / MNDWI before and after, clear-observation counts, the granules used,
                and the same statistics for a control set (see 02_render.py)

Each pixel is put into one optical class (see classify()). A first version used a single "|dNDVI| or |dMNDWI| >= 0.2"
rule; it also fired on seasonal harvest (about 55-66 % of control pixels), so it could not separate candidates from
the background. We replaced it with these classes and report candidates and controls side by side.
Optical classes are supporting evidence only; they are not ground truth.
Composites are cached in data/derived/<site>_hls.npz; pass --refresh to download again.

Reads only the needed window of each Cloud-Optimized GeoTIFF over HTTPS (Earthdata Login token, see 01_subset_gcov.py).
"""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import earthaccess
import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "data"
SITES = {
    "saemangeum": (126.42, 35.68, 126.80, 35.99),
    "yongin": (127.12, 37.04, 127.40, 37.22),
}
RES = 0.00025
WINDOWS = {"summer": ("2026-06-01", "2026-07-31"), "autumn": ("2026-10-01", "2026-11-10")}
MAX_SCENE_CLOUD = 60  # skip scenes that are mostly cloud
BANDS = {"HLSL30": {"blue": "B02", "green": "B03", "red": "B04", "nir": "B05", "swir1": "B06"},
         "HLSS30": {"blue": "B02", "green": "B03", "red": "B04", "nir": "B8A", "swir1": "B11"}}
CHANGE = 0.20
CROP = 48  # same evidence-crop half-size as 02_render.py


def grid(bb):
    w, s, e, n = bb
    return int(round((n - s) / RES)), int(round((e - w) / RES)), rasterio.transform.from_origin(w, n, RES, RES)


def read_band(fs, url, bb, shape, tr, nearest=False):
    import time
    for attempt in range(5):  # the archive occasionally answers 502/503; retry with backoff
        try:
            return _read_band(fs, url, bb, shape, tr, nearest)
        except Exception as e:
            if attempt == 4:
                raise
            print("retry", url.split("/")[-1], type(e).__name__, flush=True); time.sleep(3 * (attempt + 1))


def _read_band(fs, url, bb, shape, tr, nearest=False):
    H, W = shape
    out = np.full((H, W), np.nan, dtype="float32")
    with fs.open(url, block_size=2 ** 20, cache_type="blockcache") as f, rasterio.open(f) as src:
        b = transform_bounds("EPSG:4326", src.crs, *bb, densify_pts=21)
        win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        a = src.read(1, window=win, boundless=True, fill_value=src.nodata if src.nodata is not None else 255).astype("float32")
        if nearest:
            a[a == 255] = np.nan
        else:
            a[a == -9999] = np.nan
            a *= 1e-4
        reproject(a, out, src_transform=src.window_transform(win), src_crs=src.crs, dst_transform=tr, dst_crs="EPSG:4326",
                  resampling=Resampling.nearest if nearest else Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
    return out


def load_granule(fs, g, bb, shape, tr):
    sn = "HLS" + g["umm"]["GranuleUR"].split(".")[1]  # HLS.L30.T52SCG... -> HLSL30
    links = g.data_links(access="external")
    pick = lambda code: next(u for u in links if u.endswith(f".{code}.tif"))
    fm = read_band(fs, pick("Fmask"), bb, shape, tr, nearest=True)
    fmi = np.nan_to_num(fm, nan=255).astype("uint8")
    # bits: 1 cloud, 2 adjacent to cloud/shadow, 3 cloud shadow, 4 snow/ice
    clear = np.isfinite(fm) & ((fmi & 0b11110) == 0)
    if clear.mean() < 0.02:
        return None
    bands = {k: read_band(fs, pick(c), bb, shape, tr) for k, c in BANDS[sn].items()}
    for k in bands:
        bands[k][~clear] = np.nan
    date = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:10]
    return {"date": date, "sensor": sn, "id": g["umm"]["GranuleUR"], "bands": bands, "clear": clear}


def composite(items, shape):
    out = {}
    for k in ("blue", "green", "red", "nir", "swir1"):
        st = np.stack([it["bands"][k] for it in items])
        with np.errstate(all="ignore"):
            out[k] = np.nanmedian(st, axis=0)
    out["n"] = np.sum([np.isfinite(it["bands"]["red"]) for it in items], axis=0).astype("int16")
    with np.errstate(all="ignore"):
        out["ndvi"] = (out["nir"] - out["red"]) / (out["nir"] + out["red"])
        out["mndwi"] = (out["green"] - out["swir1"]) / (out["green"] + out["swir1"])
    return out


def true_colour(c):
    rgb = np.dstack([c["red"], c["green"], c["blue"]])
    v = np.clip(rgb / 0.22, 0, 1) ** 0.8
    alpha = np.isfinite(rgb).all(2)
    img = np.dstack([(np.nan_to_num(v) * 255).astype("uint8"), (alpha * 255).astype("uint8")])
    return img


CLASSES = ["water_to_land", "veg_to_bare", "open_both", "other"]


def classify(a, b):
    """Per-pixel optical class between the summer (a) and autumn (b) composites.
    water_to_land: MNDWI > 0 in summer and < 0 in autumn (open water or wet flat became dry ground)
    veg_to_bare:   NDVI >= 0.3 in summer and < 0.2 in autumn, not water in autumn (vegetation removed or harvested)
    open_both:     NDVI < 0.2 and MNDWI < 0 in both (ground that was already open/bare in summer; optics cannot
                   see whether something was built on it)
    other:         everything else (no clear change, greening, water that stayed water ...)"""
    ok = np.isfinite(a["ndvi"]) & np.isfinite(b["ndvi"]) & np.isfinite(a["mndwi"]) & np.isfinite(b["mndwi"])
    with np.errstate(invalid="ignore"):
        w2l = (a["mndwi"] > 0) & (b["mndwi"] < 0)
        v2b = (a["ndvi"] >= 0.3) & (b["ndvi"] < 0.2) & (b["mndwi"] < 0) & ~w2l
        ob = (a["ndvi"] < 0.2) & (b["ndvi"] < 0.2) & (a["mndwi"] < 0) & (b["mndwi"] < 0)
    cls = np.full(ok.shape, 3, dtype="int8"); cls[ob] = 2; cls[v2b] = 1; cls[w2l] = 0; cls[~ok] = -1
    return cls


def stats(mask, a, b, cls):
    ok = mask & (cls >= 0)
    if ok.sum() == 0:
        return {"px_with_clear_optics": 0}
    sh = {c: round(float((cls[ok] == k).mean()), 3) for k, c in enumerate(CLASSES)}
    return {"px_with_clear_optics": int(ok.sum()), "share": sh, "main": max(sh, key=sh.get),
            "ndvi_before": round(float(np.median(a["ndvi"][ok])), 2), "ndvi_after": round(float(np.median(b["ndvi"][ok])), 2),
            "mndwi_before": round(float(np.median(a["mndwi"][ok])), 2), "mndwi_after": round(float(np.median(b["mndwi"][ok])), 2)}


def build_composites(fs, site, bb):
    shape_h, shape_w, tr = grid(bb)
    comps, used = {}, {}
    for wname, (t0, t1) in WINDOWS.items():
        grans = []
        for sn in ("HLSL30", "HLSS30"):
            grans += earthaccess.search_data(short_name=sn, bounding_box=bb, temporal=(t0, t1), cloud_cover=(0, MAX_SCENE_CLOUD))
        with ThreadPoolExecutor(max_workers=4) as ex:
            items = [x for x in ex.map(lambda g: load_granule(fs, g, bb, (shape_h, shape_w), tr), grans) if x]
        comps[wname] = composite(items, (shape_h, shape_w))
        used[wname] = sorted({(it["date"], it["sensor"], it["id"]) for it in items})
        print(site, wname, len(items), "scenes", flush=True)
    return comps, used


def main():
    import sys
    cache = ROOT / "data" / "derived"
    fs = None
    result = {"classes": classify.__doc__, "windows": WINDOWS, "product": "HLS v2.0 (HLSL30 + HLSS30), LP DAAC", "sites": {}}
    for site, bb in SITES.items():
        cf = cache / f"{site}_hls.npz"
        if cf.exists() and "--refresh" not in sys.argv:  # composites are cached; analysis reruns offline
            z = np.load(cf, allow_pickle=True)
            comps = {w: {k: z[f"{w}_{k}"].astype("float32") for k in ("blue", "green", "red", "nir", "swir1", "ndvi", "mndwi", "n")} for w in WINDOWS}
            used = json.loads(str(z["used"]))
        else:
            if fs is None:
                tok = Path.home() / ".earthdata_token"  # local only, never committed
                if tok.exists() and not os.getenv("EARTHDATA_TOKEN"):
                    os.environ["EARTHDATA_TOKEN"] = tok.read_text().strip()
                earthaccess.login(strategy="environment" if os.getenv("EARTHDATA_TOKEN") else "netrc")
                fs = earthaccess.get_fsspec_https_session()
            comps, used = build_composites(fs, site, bb)
            np.savez_compressed(cf, used=json.dumps(used), **{f"{w}_{k}": v.astype("float16") for w, c in comps.items() for k, v in c.items()})
        for wname in WINDOWS:
            Image.fromarray(true_colour(comps[wname]), "RGBA").save(WEB / site / f"hls_{wname}.webp", "WEBP", quality=80, method=4)
        a, b = comps["summer"], comps["autumn"]
        cls = classify(a, b)
        pz = np.load(ROOT / "data" / "derived" / f"{site}_patches.npz")
        ids, control = pz["ids"], pz["control"]
        H, W = ids.shape
        spots = {}
        for i in range(1, int(ids.max()) + 1):
            m = ids == i
            s = stats(m, a, b, cls)
            s["clear_obs_summer"] = int(np.median(a["n"][m])); s["clear_obs_autumn"] = int(np.median(b["n"][m]))
            spots[str(i)] = s
            if i <= 12:
                ys, xs = np.nonzero(m); cy, cx = int(ys.mean()), int(xs.mean())
                ya, yb, xa, xb = max(0, cy - CROP), min(H, cy + CROP), max(0, cx - CROP), min(W, cx + CROP)
                for tag, wname in (("before", "summer"), ("after", "autumn")):
                    im = Image.open(WEB / site / f"hls_{wname}.webp").convert("RGB").crop((xa, ya, xb, yb))
                    im = im.resize(((xb - xa) * 2, (yb - ya) * 2), Image.NEAREST)
                    im.save(WEB / site / "spots" / f"{i}_hls_{tag}.webp", "WEBP", quality=85)
        with np.errstate(invalid="ignore"):
            land = a["mndwi"] < 0
        result["sites"][site] = {
            "granules": {k: [{"date": d, "sensor": s, "id": g} for d, s, g in v] for k, v in used.items()},
            "candidates_all_pixels": stats(ids > 0, a, b, cls),
            "control_pixels": stats(control, a, b, cls),
            "control_land_pixels": stats(control & land, a, b, cls),
            "spots": spots,
        }
        r = result["sites"][site]
        print(site, "cand", r["candidates_all_pixels"].get("share"), "| ctrl", r["control_pixels"].get("share"), "| ctrl land", r["control_land_pixels"].get("share"), flush=True)
        print("  patches:", [(k, v.get("main"), v.get("px_with_clear_optics")) for k, v in spots.items()], flush=True)
    json.dump(result, open(WEB / "optical.json", "w"), indent=1)


if __name__ == "__main__":
    main()
