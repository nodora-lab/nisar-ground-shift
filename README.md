# Ground Shift — watching land change with NISAR radar

NASA Space Apps Challenge 2026 · Challenge: **Dancing with the SARs** · Team: CIELIEN

**Live site:** https://nodora-lab.github.io/nisar-ground-shift/

## What it is
An interactive web map that uses NISAR L-band radar (Level-2 GCOV backscatter, HH and HV) to explore surface change linked to large land-development projects over one year, at two places in Korea:

- **Saemangeum** — tidal flats behind a sea wall turning into reclaimed land, roads and ports.
- **Yongin** — farmland and forested hills being graded for semiconductor clusters.

Both sites sit in the same NISAR scene (descending track 133, frame 70), so 18 radar dates from Oct 2025 to Nov 2026 cover both.

What you can do on the site:
- Step or play through the 18 acquisitions on a time-true timeline. Gaps are marked, and each date is tagged BETA / PROVISIONAL / VALIDATED.
- Switch between five layers: RGB composite, HH, HV, HH change (vs. Jun 23, 2026, the first PROVISIONAL date), and **persistent HH-brightening candidates**.
- Open an **evidence card** for each candidate patch: area, coordinates, patch-median HH on all 18 dates, and before/after crops.
- Compare any two dates with a swipe slider. You get a warning when you mix uncalibrated and calibrated dates.
- Follow a trend chart of median HH / HV for the area. The line breaks at the BETA boundary.
- Read what each colour can mean for that place, plus the full data & method page with its limits.
- Download candidates as GeoJSON: `web/data/<site>_candidates.geojson`.

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
To add a new place, add its bounding box to `SITES` in scripts 01 and 02, add a text block in `web/content.js`, and rerun the scripts.

## Method (short)
1. Remote subsetting of HDF5 over HTTPS (no full downloads).
2. 5 × 5 boxcar speckle filter on linear power.
   The window is 50 m, on the native 10 m UTM grid.
3. Area-averaged reprojection to EPSG:4326 at 0.00025° (about 28 m N–S × 22 m E–W here), then conversion to dB.
4. RGB = HH / HV / HH(dB)−HV(dB), with one fixed stretch for all dates.
5. Change = HH(date) − HH(Jun 23, 2026), shown where |Δ| ≥ 2 dB.
6. Persistent-brightening candidates:
   - HH ≤ −8 dB on **all** of Jun 23, Jul 5 and Jul 17, 2026, and ≥ −3 dB on **all** of Oct 9, Oct 21 and Nov 2, 2026
   - patches use 1-px dilation, 8-connectivity and at least 4 pixels
   - area = pixel count × pixel cell area
   - thresholds were set once and not tuned against construction maps
7. Consistency check: the three largest Yongin patches fall inside the area OpenStreetMap maps as the Yongin Semiconductor Cluster construction site. This is a single check, not an accuracy assessment.

Limits:
- BETA data (Oct 2025 – Jan 2026) is uncalibrated.
- "VALIDATED" is the NISAR product's maturity, not a validation of our test.
- Our set has no acquisitions from Jan 18 to Jun 23, 2026, and NISAR has an instrument gap from Jul 27 to Aug 10, 2026.
- Backscatter change is not land-use change: wind, rain, soil moisture, crops and geometry also matter.
- Candidate hectares count pixels that passed the test, not measured footprints.
- False-positive rates have not been measured.

See the Data & method page on the site.

## Use of Super Intelligence (SI)
We used SI assistants (Claude, ChatGPT) to help draft code and English text and to check facts; the team reviewed all of it. All radar overlays come from real NISAR data through the scripts in this repository. No SI-generated imagery is used in the map views.

## License
Apache-2.0
