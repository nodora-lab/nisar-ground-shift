"""Subset NISAR L2 GCOV (HH, HV backscatter) over study sites without downloading full files.

Reads only the needed HDF5 chunks over HTTPS (Earthdata Login via ~/.netrc / %USERPROFILE%\\_netrc).
Outputs one small GeoTIFF per site / date / polarization into data/subsets/.

SI note: drafted with SI assistance (Claude) and reviewed by the team.
"""
import json, sys, os, re, time
from pathlib import Path
import numpy as np
import h5py, fsspec, earthaccess
import rasterio
from rasterio.transform import from_origin
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "subsets"
OUT.mkdir(parents=True, exist_ok=True)

# lon_min, lat_min, lon_max, lat_max
SITES = {
    "saemangeum": (126.42, 35.68, 126.80, 35.99),
    "yongin": (127.12, 37.04, 127.40, 37.22),
}
GRID = "/science/LSAR/GCOV/grids/frequencyA"


def site_window(x, y, epsg, bbox):
    t = Transformer.from_crs(4326, epsg, always_xy=True)
    xs, ys = t.transform([bbox[0], bbox[2], bbox[0], bbox[2]], [bbox[1], bbox[1], bbox[3], bbox[3]])
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    ix = np.where((x >= xmin) & (x <= xmax))[0]
    iy = np.where((y >= ymin) & (y <= ymax))[0]
    if len(ix) == 0 or len(iy) == 0:
        return None
    return slice(iy[0], iy[-1] + 1), slice(ix[0], ix[-1] + 1)


def process(url, date, fs):
    done = all((OUT / f"{s}_{date}_{p}.tif").exists() for s in SITES for p in ("HH", "HV"))
    if done:
        print(date, "already done"); return
    t0 = time.time()
    with fs.open(url, "rb", block_size=8 * 1024 * 1024, cache_type="blockcache") as f:
        with h5py.File(f, "r") as h:
            g = h[GRID]
            x = g["xCoordinates"][:]; y = g["yCoordinates"][:]
            epsg = int(g["projection"].attrs.get("epsg_code", g["projection"][()]))
            meta = {"epsg": epsg, "dx": float(x[1] - x[0]), "dy": float(y[1] - y[0])}
            for s, bbox in SITES.items():
                w = site_window(x, y, epsg, bbox)
                if w is None:
                    print(date, s, "not in frame"); continue
                ys_, xs_ = w
                tr = from_origin(x[xs_.start] - meta["dx"] / 2, y[ys_.start] - meta["dy"] / 2, meta["dx"], abs(meta["dy"]))
                for pol, ds in (("HH", "HHHH"), ("HV", "HVHV")):
                    if ds not in g:
                        print(date, s, ds, "missing"); continue
                    a = g[ds][ys_, xs_].astype("float32")
                    p = OUT / f"{s}_{date}_{pol}.tif"
                    with rasterio.open(p, "w", driver="GTiff", height=a.shape[0], width=a.shape[1], count=1,
                                       dtype="float32", crs=f"EPSG:{epsg}", transform=tr, compress="deflate", nodata=np.nan) as dst:
                        dst.write(a, 1)
                print(date, s, a.shape, f"{time.time() - t0:.0f}s")
    return meta


def main():
    tok = Path.home() / ".earthdata_token"  # local only, never committed
    if tok.exists() and not os.getenv("EARTHDATA_TOKEN"):
        os.environ["EARTHDATA_TOKEN"] = tok.read_text().strip()
    earthaccess.login(strategy="environment" if os.getenv("EARTHDATA_TOKEN") else "netrc")
    fs = earthaccess.get_fsspec_https_session()
    res = json.load(open(ROOT / "data" / "search_result.json"))
    rows = res["saemangeum"]["133/70/DESCENDING"]
    only = sys.argv[1:]  # optional list of dates
    for r in rows:
        date, url = r[0], r[3]
        if only and date not in only:
            continue
        try:
            process(url, date, fs)
        except Exception as e:
            print(date, "ERROR", repr(e)[:300])


if __name__ == "__main__":
    main()
