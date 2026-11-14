# Ground Shift — watching land change with NISAR radar

NASA Space Apps Challenge 2026 · Challenge: **Dancing with the SARs** · Team: CIELIEN

**Live site:** https://nodora-lab.github.io/nisar-ground-shift/

## What it is
An interactive web map that uses NISAR L-band radar (Level-2 GCOV backscatter, HH and HV) to show how large human projects reshape natural land over one year, at two places in Korea:

- **Saemangeum** — tidal flats behind a sea wall turning into reclaimed land, roads and ports.
- **Yongin** — farmland and forested hills being graded for semiconductor clusters.

Both sites sit in the same NISAR scene (descending track 133, frame 70), so 18 radar dates from Oct 2025 to Nov 2026 cover both.

What you can do on the site:
- Step or play through every radar date on a time-true timeline (data gaps shown honestly).
- Switch layers: RGB composite, HH, HV, and an HH change layer (±2 dB or more vs. the first calibrated date).
- Compare any two dates with a swipe slider.
- Follow a trend chart of median HH / HV backscatter for the area.
- Read what each colour means for that place, plus the full data & method page with limits.

## Data
- NISAR L2 GCOV — collections `NISAR_L2_GCOV_BETA_V1`, `NISAR_L2_GCOV_PROVISIONAL_V1`, `NISAR_L2_GCOV_V1` — NASA Alaska Satellite Facility DAAC, accessed with Earthdata Login.
- Basemap: Esri World Dark Gray Canvas (© Esri, HERE, Garmin, © OpenStreetMap contributors).

## How to run it yourself
Requires Python 3.11+ and a free [Earthdata Login](https://urs.earthdata.nasa.gov/).

```bash
pip install asf_search earthaccess h5py fsspec rasterio pyproj scipy pillow numpy
python scripts/00_search.py            # find GCOV files over the sites -> search_result.json
python scripts/01_subset_gcov.py       # read only the study-area chunks of each ~6 GB file
python scripts/02_render.py            # web images + web/data/sites.json
python -m http.server -d web 8000      # open http://localhost:8000
```

Credentials are read from `~/.netrc` (or the `EARTHDATA_TOKEN` environment variable). Never commit them.
To add a new place, add a bounding box to `SITES` in scripts 01 and 02 and a text block in `web/content.js`.

## Method (short)
1. Remote subsetting of HDF5 over HTTPS (no full downloads).
2. 5 × 5 boxcar speckle filter on linear power.
3. Reprojection to EPSG:4326 at 0.00025° (≈25 m), conversion to dB.
4. RGB = HH / HV / HH−HV with one fixed stretch for all dates.
5. Change = HH(date) − HH(Jun 23, 2026), shown where |Δ| ≥ 2 dB.

Limits: BETA data (Oct 2025 – Jan 2026) is uncalibrated; no public data Jan 20 – Jun 17, 2026; instrument gap Jul 27 – Aug 10, 2026; backscatter change is not the same as land-use change (wind, rain, soil moisture and crops also matter). See the Data & method page on the site.

## Use of Super Intelligence (SI)
We used SI assistants (Claude, ChatGPT) to help draft code and English text and to check facts; the team reviewed all of it. All maps and radar images come from real NISAR data through the scripts in this repository. No SI-generated imagery is used in the map views.

## License
Apache-2.0
