"""Independent optical cross-check with NASA HLS (Harmonized Landsat and Sentinel-2, v2.0).

For each site we build two seasonal clear-sky reference composites on the same 0.00025 deg grid as the radar images:
  summer = 2026-06-01 .. 2026-07-31 (around the radar's early dates Jun 23 - Jul 17)
  autumn = 2026-10-01 .. 2026-11-02 (the radar's late dates Oct 9 - Nov 2; nothing after the last radar date)
These are seasonal references, not images taken on a radar date.

Quality masking happens on each scene's own 30 m grid BEFORE reprojection: a pixel is kept only when HLS Fmask shows
no cloud, adjacent cloud/shadow, cloud shadow or snow/ice, and the aerosol level is not "high". NDVI and MNDWI are
computed per observation and their per-pixel medians are used; true colour uses per-band medians.

Index classes (descriptive, NOT land-use labels):
  mndwi_pos_to_neg  MNDWI > 0 in summer and < 0 in autumn (water-like surface no longer water-like: fill, structures,
                    drainage of a paddy, mixed pixels ...)
  ndvi_high_to_low  NDVI >= 0.3 in summer, NDVI < 0.2 and MNDWI < 0 in autumn (vegetation signal lost: clearing, harvest ...)
  low_ndvi_both     NDVI < 0.2 and MNDWI < 0 in both seasons (low vegetation in both: bare, built or other covers)
  other             everything else
A first rule (|dNDVI| or |dMNDWI| >= 0.2) also fired often in comparison cells (seasonal harvest); its results are
kept in optical.json ("first_rule_share_changed"). The classes above were defined after seeing that, so every
comparison here is exploratory, not an accuracy assessment.

Comparison cells: all six radar dates present, HH <= -8 dB on all three summer dates, did NOT pass the autumn test,
>= 3 px from any candidate (from 02_render.py); "within_2km" additionally keeps only cells within 2 km of a candidate.
Rates are reported within summer optical strata (water-like / vegetated / low vegetation in summer), with denominators.

Outputs (web/data): <site>/hls_summer.webp, <site>/hls_autumn.webp; evidence crops for the 12 largest patches with the
patch outline drawn on both the radar and the optical crops (overwrites the plain radar crops from 02_render.py);
optical.json. Composites are cached in data/derived/<site>_hls.npz (pass --refresh to download again).
Reads only the needed window of each Cloud-Optimized GeoTIFF over HTTPS with Earthdata Login.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import earthaccess
import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import from_bounds
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "data"
SITES = {
    "saemangeum": (126.42, 35.68, 126.80, 35.99),
    "yongin": (127.12, 37.04, 127.40, 37.22),
}
RES = 0.00025
WINDOWS = {"summer": ("2026-06-01", "2026-07-31"), "autumn": ("2026-10-01", "2026-11-02")}
MAX_SCENE_CLOUD = 60  # skip scenes that are mostly cloud
BANDS = {"HLSL30": {"blue": "B02", "green": "B03", "red": "B04", "nir": "B05", "swir1": "B06"},
         "HLSS30": {"blue": "B02", "green": "B03", "red": "B04", "nir": "B8A", "swir1": "B11"}}
KEYS = ("blue", "green", "red", "nir", "swir1", "ndvi", "mndwi")
CLASSES = ["mndwi_pos_to_neg", "ndvi_high_to_low", "low_ndvi_both", "other"]
CROP = 48  # same evidence-crop half-size as 02_render.py
NEAR_PX = 80  # ~2 km at ~25 m cells


def grid(bb):
    w, s, e, n = bb
    return int(round((n - s) / RES)), int(round((e - w) / RES)), rasterio.transform.from_origin(w, n, RES, RES)


def retry(fn, *args):
    for attempt in range(5):  # the archive occasionally answers 502/503; retry with backoff
        try:
            return fn(*args)
        except Exception as e:
            if attempt == 4:
                raise
            print("retry", type(e).__name__, flush=True)
            time.sleep(3 * (attempt + 1))


def read_native(fs, url, bb):
    """Read the study-area window of one COG on its own grid."""
    with fs.open(url, block_size=2 ** 20, cache_type="blockcache") as f, rasterio.open(f) as src:
        b = transform_bounds("EPSG:4326", src.crs, *bb, densify_pts=21)
        win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        nod = src.nodata
        a = src.read(1, window=win, boundless=True, fill_value=nod if nod is not None else 255)
        return a, src.window_transform(win), src.crs


def to_grid(a, src_tr, crs, shape, tr):
    out = np.full(shape, np.nan, dtype="float32")
    reproject(a, out, src_transform=src_tr, src_crs=crs, dst_transform=tr, dst_crs="EPSG:4326",
              resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
    return out


def load_granule(fs, g, bb, shape, tr):
    sn = "HLS" + g["umm"]["GranuleUR"].split(".")[1]  # HLS.L30.T52SCG... -> HLSL30
    links = g.data_links(access="external")
    pick = lambda code: next(u for u in links if u.endswith(f".{code}.tif"))
    fm, _, _ = retry(read_native, fs, pick("Fmask"), bb)
    fm = fm.astype("uint8")
    # Fmask bits: 1 cloud, 2 adjacent to cloud/shadow, 3 cloud shadow, 4 snow/ice, 6-7 aerosol level (3 = high)
    clear = (fm != 255) & ((fm & 0b11110) == 0) & ((fm >> 6) != 3)
    if clear.mean() < 0.02:
        return None
    native = {}
    for k, c in BANDS[sn].items():
        a, btr, crs = retry(read_native, fs, pick(c), bb)
        a = a.astype("float32")
        a[(a == -9999) | ~clear] = np.nan  # mask on the scene's own grid, before any resampling
        native[k] = a * 1e-4
    with np.errstate(all="ignore"):
        native["ndvi"] = (native["nir"] - native["red"]) / (native["nir"] + native["red"])
        native["mndwi"] = (native["green"] - native["swir1"]) / (native["green"] + native["swir1"])
    bands = {k: to_grid(v, btr, crs, shape, tr) for k, v in native.items()}
    date = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:10]
    return {"date": date, "sensor": sn, "id": g["umm"]["GranuleUR"], "bands": bands}


def composite(items):
    out = {}
    for k in KEYS:  # indices: median of per-observation values; true colour: per-band medians
        st = np.stack([it["bands"][k] for it in items])
        with np.errstate(all="ignore"):
            out[k] = np.nanmedian(st, axis=0)
    out["n"] = np.sum([np.isfinite(it["bands"]["ndvi"]) for it in items], axis=0).astype("int16")
    return out


def true_colour(c):
    rgb = np.dstack([c["red"], c["green"], c["blue"]])
    v = np.clip(rgb / 0.22, 0, 1) ** 0.8
    alpha = np.isfinite(rgb).all(2)
    return np.dstack([(np.nan_to_num(v) * 255).astype("uint8"), (alpha * 255).astype("uint8")])


def classify(a, b):
    ok = np.isfinite(a["ndvi"]) & np.isfinite(b["ndvi"]) & np.isfinite(a["mndwi"]) & np.isfinite(b["mndwi"])
    with np.errstate(invalid="ignore"):
        w2l = (a["mndwi"] > 0) & (b["mndwi"] < 0)
        v2b = (a["ndvi"] >= 0.3) & (b["ndvi"] < 0.2) & (b["mndwi"] < 0) & ~w2l
        ob = (a["ndvi"] < 0.2) & (b["ndvi"] < 0.2) & (a["mndwi"] < 0) & (b["mndwi"] < 0)
    cls = np.full(ok.shape, 3, dtype="int8")
    cls[ob] = 2; cls[v2b] = 1; cls[w2l] = 0; cls[~ok] = -1
    return cls


def stats(mask, a, b, cls):
    ok = mask & (cls >= 0)
    out = {"cells_total": int(mask.sum()), "cells_with_optics": int(ok.sum())}
    if ok.sum() == 0:
        return out
    sh = {c: round(float((cls[ok] == k).mean()), 3) for k, c in enumerate(CLASSES)}
    with np.errstate(invalid="ignore"):
        first = (np.abs(b["ndvi"][ok] - a["ndvi"][ok]) >= 0.2) | (np.abs(b["mndwi"][ok] - a["mndwi"][ok]) >= 0.2)
        wet = ok & (a["mndwi"] > 0)
        veg = ok & (a["ndvi"] >= 0.3) & (a["mndwi"] <= 0)
        low = ok & (a["ndvi"] < 0.2) & (a["mndwi"] < 0)
    out.update({
        "share": sh, "main": max(sh, key=sh.get),
        "strata": {
            "water_like_in_summer": {"n": int(wet.sum()), "k": int((wet & (cls == 0)).sum()), "event": "MNDWI turned negative"},
            "vegetated_in_summer": {"n": int(veg.sum()), "k": int((veg & (cls == 1)).sum()), "event": "NDVI fell below 0.2"},
            "low_vegetation_in_summer": {"n": int(low.sum()), "k": int((low & (cls == 2)).sum()), "event": "stayed low in autumn"},
        },
        "first_rule_share_changed": round(float(first.mean()), 3),
        "ndvi_before": round(float(np.median(a["ndvi"][ok])), 2), "ndvi_after": round(float(np.median(b["ndvi"][ok])), 2),
        "mndwi_before": round(float(np.median(a["mndwi"][ok])), 2), "mndwi_after": round(float(np.median(b["mndwi"][ok])), 2),
    })
    return out


def outlined(img, m, scale=2, color=(255, 159, 67)):
    """Upscale a crop and draw a ring just outside the candidate cells, so the cells themselves stay visible."""
    ring = binary_dilation(m, iterations=2) & ~binary_dilation(m, iterations=1)
    arr = np.array(img.convert("RGB").resize((img.width * scale, img.height * scale), Image.NEAREST))
    arr[np.kron(ring, np.ones((scale, scale), dtype=bool)).astype(bool)] = color
    return Image.fromarray(arr)


def build_composites(fs, site, bb):
    shape_h, shape_w, tr = grid(bb)
    comps, used = {}, {}
    for wname, (t0, t1) in WINDOWS.items():
        grans = []
        for sn in ("HLSL30", "HLSS30"):
            grans += earthaccess.search_data(short_name=sn, bounding_box=bb, temporal=(t0, t1), cloud_cover=(0, MAX_SCENE_CLOUD))
        with ThreadPoolExecutor(max_workers=4) as ex:
            items = [x for x in ex.map(lambda g: load_granule(fs, g, bb, (shape_h, shape_w), tr), grans) if x]
        comps[wname] = composite(items)
        used[wname] = sorted({(it["date"], it["sensor"], it["id"]) for it in items})
        print(site, wname, len(items), "scenes", flush=True)
    return comps, used


def main():
    cache = ROOT / "data" / "derived"
    fs = None
    result = {"product": "HLS v2.0 (HLSL30 + HLSS30), LP DAAC", "windows": WINDOWS,
              "qa": "Fmask applied on each scene's native grid before reprojection: no cloud, adjacent cloud/shadow, cloud shadow, snow/ice; aerosol not high",
              "classes": {"mndwi_pos_to_neg": "MNDWI > 0 in summer and < 0 in autumn",
                          "ndvi_high_to_low": "NDVI >= 0.3 in summer; NDVI < 0.2 and MNDWI < 0 in autumn",
                          "low_ndvi_both": "NDVI < 0.2 and MNDWI < 0 in both seasons", "other": "everything else"},
              "first_rule": "|dNDVI| >= 0.2 or |dMNDWI| >= 0.2 (abandoned: fired on seasonal harvest)",
              "comparison": "all six radar dates, HH <= -8 dB on all summer dates, failed the autumn test, >= 3 px from candidates; within_2km also <= 2 km from a candidate",
              "sites": {}}
    for site, bb in SITES.items():
        cf = cache / f"{site}_hls.npz"
        if cf.exists() and "--refresh" not in sys.argv:  # composites are cached; analysis reruns offline
            z = np.load(cf)
            comps = {w: {k: z[f"{w}_{k}"].astype("float32") for k in KEYS + ("n",)} for w in WINDOWS}
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
        pz = np.load(cache / f"{site}_patches.npz")
        ids, control = pz["ids"], pz["control"]
        near = distance_transform_edt(ids == 0) <= NEAR_PX
        sj = next(x for x in json.load(open(WEB / "sites.json"))["sites"] if x["id"] == site)
        H, W = ids.shape
        spots = {}
        for i in range(1, int(ids.max()) + 1):
            m = ids == i
            s = stats(m, a, b, cls)
            s["clear_obs_summer"] = int(np.median(a["n"][m])); s["clear_obs_autumn"] = int(np.median(b["n"][m]))
            spots[str(i)] = s
            if i <= 12:
                ys, xs = np.nonzero(m); cy, cx = int(round(ys.mean())), int(round(xs.mean()))
                ya, yb, xa, xb = max(0, cy - CROP), min(H, cy + CROP), max(0, cx - CROP), min(W, cx + CROP)
                srcs = {"before": f"{sj['new_early'][0]}_rgb.webp", "after": f"{sj['new_late'][-1]}_rgb.webp",
                        "hls_before": "hls_summer.webp", "hls_after": "hls_autumn.webp"}
                for tag, fn in srcs.items():
                    im = Image.open(WEB / site / fn).convert("RGB").crop((xa, ya, xb, yb))
                    outlined(im, m[ya:yb, xa:xb]).save(WEB / site / "spots" / f"{i}_{tag}.webp", "WEBP", quality=85)
        result["sites"][site] = {
            "granules": {k: [{"date": d, "sensor": s_, "id": g} for d, s_, g in v] for k, v in used.items()},
            "candidates": stats(ids > 0, a, b, cls),
            "comparison_all": stats(control, a, b, cls),
            "comparison_within_2km": stats(control & near, a, b, cls),
            "spots": spots,
        }
        r = result["sites"][site]
        for k in ("candidates", "comparison_all", "comparison_within_2km"):
            print(site, k, r[k]["cells_total"], r[k]["cells_with_optics"], r[k].get("share"), r[k].get("first_rule_share_changed"), flush=True)
            print("   strata", r[k].get("strata"), flush=True)
        print("  patches:", [(k, v.get("main"), v["cells_with_optics"], v["clear_obs_summer"]) for k, v in spots.items()], flush=True)
    json.dump(result, open(WEB / "optical.json", "w"), indent=1)


if __name__ == "__main__":
    main()
