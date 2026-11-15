// Text content for Ground Shift. SI note: English text drafted with SI assistance (Claude, ChatGPT) and reviewed by the team.
window.CONTENT = {
  gaps: [
    { from: "2026-01-20", to: "2026-06-17", short: "no acquisitions in our set", label: "Our dataset has no acquisitions between the last BETA date (Jan 18, 2026) and the first PROVISIONAL date (Jun 23, 2026)" },
    { from: "2026-07-27", to: "2026-08-10", short: "instrument gap", label: "NISAR instrument data gap, Jul 27 – Aug 10, 2026" }
  ],
  sites: {
    saemangeum: {
      chip: "Saemangeum", color: "var(--teal)",
      short: "Tidal flats → reclaimed land, roads and ports",
      kicker: "STUDY AREA 1 OF 2",
      finding: "Radar finding: {ha} ha of pixels passed our persistent-brightening test between summer and autumn 2026, in {n} patches across the reclaimed area and its edges in Gunsan and Buan. These are candidates, not measured construction footprints.",
      title: "Saemangeum: a tidal flat becoming land",
      meta: "West coast of Korea · 35.8°N, 126.6°E · NISAR descending track 133, frame 70",
      signals: [
        ["var(--up)", "Brighter in HH", "Walls and buildings next to flat ground can send the radar straight back (double bounce). Rough fill and wet soil can also brighten HH."],
        ["var(--down)", "Darker", "Calm water and very smooth, flattened sand can reflect the signal away from the satellite."],
        ["var(--prov)", "HV changes", "Cross-polarised (HV) signal can rise with vegetation and rough fill, and fall when land is scraped bare."]
      ],
      why: "Saemangeum was a major feeding and resting site for migratory shorebirds on the East Asian–Australasian Flyway, and their numbers fell sharply after the sea wall closed. The area is still being developed today. Radar sees through clouds and works at night, so anyone can explore radar changes that may be linked to this development.",
      facts: [
        ["The 33.9 km sea wall closed in 2006 and was completed in 2010. Before that, the area was tidal flats and the estuaries of the Mangyeong and Dongjin rivers.", "https://saemangeum.go.kr/sda/en/content.do?key=2010214151548", "Saemangeum Development Agency"],
        ["Great Knots and Spoon-billed Sandpipers were among the shorebirds that declined after closure.", "https://doi.org/10.1071/MU16006", "Emu (2016)"],
        ["2026 work plan: industrial-land reclamation, a regional connecting road, and the new port, where two berths are complete.", "https://www.saemangeum.go.kr/sda/brd/view.do?key=2009074409621&nttSn=10702", "Agency 2026 plan"],
        ["A revised master plan (Oct 28, 2026) sets 169.6 km² for reclamation and development by 2035.", "https://www.opm.go.kr/opm/news/press-release.do?articleNo=163983&mode=view", "Prime Minister's Office"]
      ]
    },
    yongin: {
      chip: "Yongin", color: "var(--up)",
      short: "Farmland and hills → semiconductor clusters",
      kicker: "STUDY AREA 2 OF 2",
      finding: "Radar finding: our test uses only radar thresholds, with no construction boundaries as input. Its three largest patches fall inside the area that OpenStreetMap maps as the Yongin Semiconductor Cluster construction site in Wonsam-myeon. This is a consistency check, not an accuracy measurement.",
      title: "Yongin: farmland making way for chip factories",
      meta: "South of Seoul · 37.1°N, 127.3°E · same NISAR track and dates",
      signals: [
        ["var(--up)", "Brighter in HH", "Steel frames and concrete walls can create strong double-bounce returns."],
        ["var(--down)", "Darker", "Graded, compacted ground can be smoother than fields and forest, but moisture and slope also matter."],
        ["var(--prov)", "HV drops", "When trees and crops are removed, there is often less volume scattering."]
      ],
      why: "Two chip clusters are being built here, together covering about 12 km² of hills, forest and farmland. Projects this large change land, water and traffic for whole towns. A free, repeatable radar view helps residents and planners explore the pace of change themselves.",
      facts: [
        ["SK hynix cluster, Wonsam-myeon (Godang-ri, Dokseong-ri, Jukneung-ri): 4,155,996 m². Site works began on Apr 26, 2022, and the first fab on Feb 24, 2025.", "https://www.yongin.go.kr/home/www/www19/www19_02_01/www19_02_01_02.jsp", "Yongin City"],
        ["Its first cleanroom is targeted to open in Feb 2027.", "https://news.skhynix.com/en/new-facility-investment-for-yongin-semiconductor-cluster/", "SK hynix"],
        ["National semiconductor complex, Idong-eup and Namsa-eup: about 7.78 million m², planned for six fabs.", "https://www.yna.co.kr/view/AKR20260901049800003", "Yonhap"],
        ["Compensation talks began on Dec 22, 2025. Official works on Section 1 (3.45 million m²) began on Oct 28, 2026, with tree clearing reported about a month earlier.", "https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbsCode=1020&q_bbscttSn=20261102080624453", "Yongin City"]
      ]
    }
  },
  legend: {
    rgb: { title: "RGB COMPOSITE", items: [["#ff5a5a", "Red = HH (−24 to +2 dB)"], ["#5aff8a", "Green = HV (−30 to −6 dB)"], ["#5a8aff", "Blue = HH/HV power ratio, shown as HH(dB) − HV(dB)"]] },
    hh: { title: "HH BACKSCATTER", items: [["linear-gradient(90deg,#000,#fff)", "−24 dB → +2 dB"]] },
    hv: { title: "HV BACKSCATTER", items: [["linear-gradient(90deg,#000,#fff)", "−30 dB → −6 dB"]] },
    new: { title: "PERSISTENT HH BRIGHTENING · CANDIDATES", items: [["#FF9F43", "HH ≤ −8 dB on all 3 summer dates (Jun 23, Jul 5, Jul 17) and ≥ −3 dB on all 3 autumn dates (Oct 9, Oct 21, Nov 2). {ha} ha in {n} patches. Click a circle for its evidence (largest 12 shown)."], ["transparent", "Requiring all six dates reduces short-lived effects. Seasonal and processing effects can still pass, and false-positive rates have not been measured."]] },
    chg: { title: "HH CHANGE VS. JUN 23, 2026 (FIRST PROVISIONAL DATE)", items: [["#FF9F43", "Brighter by ≥ 2 dB"], ["#4DA3FF", "Darker by ≥ 2 dB"], ["transparent", "Includes crop-season effects. BETA dates are uncalibrated, so their change values are not meaningful."]] }
  },
  method: `<h2>Data &amp; method</h2>
<p>All radar overlays on this site are computed from free NISAR data. The basemap is provided by Esri. No SI-generated imagery is used in the map views.</p>
<h3>Data</h3>
<table>
<tr><th>Product</th><td>NISAR Level-2 GCOV (Geocoded Polarimetric Covariance), L-band, frequency A, HH and HV terms, 10 m posting in UTM zone 52N</td></tr>
<tr><th>Archive</th><td><a href="https://search.asf.alaska.edu/" target="_blank" rel="noopener">NASA Alaska Satellite Facility DAAC</a>, collections NISAR_L2_GCOV_BETA_V1 (7 dates), NISAR_L2_GCOV_PROVISIONAL_V1 (10 dates), NISAR_L2_GCOV_V1 (1 date). The full list of files is in <a href="https://github.com/nodora-lab/nisar-ground-shift/blob/main/data/search_result.json" target="_blank" rel="noopener">data/search_result.json</a>.</td></tr>
<tr><th>Geometry</th><td>Descending track 133, frame 70. One radar frame covers both study areas.</td></tr>
<tr><th>Dates</th><td>The 18 acquisitions we found for this track and frame, Oct 26, 2025 – Nov 2, 2026</td></tr>
<tr><th>Basemap</th><td>Esri World Dark Gray Canvas (© Esri, HERE, Garmin, © OpenStreetMap contributors), labels and background only</td></tr>
</table>
<h3>Processing</h3>
<ol>
<li><b>Read only what we need.</b> Each GCOV file is about 6 GB. We open it over HTTPS with Earthdata Login and read only the HDF5 chunks inside each study area (<code>scripts/01_subset_gcov.py</code>).</li>
<li><b>Reduce speckle.</b> 5 × 5 moving-average filter (a 50 m window) on linear backscatter, in the product's native 10 m grid.</li>
<li><b>Put every date on one grid.</b> Reproject to latitude/longitude at 0.00025° spacing (about 28 m north–south and 22–23 m east–west here, by area averaging) and convert to decibels (<code>scripts/02_render.py</code>). Pixel spacing is not the same as effective resolution: after filtering, details smaller than the 50 m filter window are smoothed out.</li>
<li><b>Colour.</b> RGB = HH (−24 to +2 dB), HV (−30 to −6 dB), HH − HV in dB (0 to 18 dB). The same fixed stretch is used for every date, so colours can be compared over time.</li>
<li><b>Change layer.</b> HH on each date minus HH on Jun 23, 2026 (the first PROVISIONAL date). Only differences of 2 dB or more are coloured. The colour gets stronger up to 10 dB.</li>
<li><b>Persistent-brightening candidates.</b> A pixel is a candidate when its HH is ≤ −8 dB on <i>all</i> of Jun 23, Jul 5 and Jul 17, 2026, and ≥ −3 dB on <i>all</i> of Oct 9, Oct 21 and Nov 2, 2026. Only calibrated (PROVISIONAL or VALIDATED) dates are used. Candidates are grouped into patches: one-pixel dilation, 8-connectivity, and at least 4 original pixels per patch. Area = number of candidate pixels × the size of a pixel cell at the site's latitude. Each patch has an evidence card: the median HH of its pixels on all 18 dates, and before/after image crops. The patches can be downloaded as GeoJSON (<a href="data/saemangeum_candidates.geojson">Saemangeum</a>, <a href="data/yongin_candidates.geojson">Yongin</a>). The thresholds were chosen once, by looking at typical HH levels. They were not tuned against construction maps.</li>
<li><b>Consistency check.</b> We looked up each Yongin patch on OpenStreetMap. The three largest fall inside the area mapped as the Yongin Semiconductor Cluster construction site. This is a single check, not an accuracy assessment.</li>
<li><b>Trend chart.</b> Median HH and HV (dB) over the whole study area on each date. The line breaks between BETA and later dates because their calibration differs.</li>
</ol>
<h3>Limits — please read before drawing conclusions</h3>
<ul>
<li><b>BETA dates are not calibrated.</b> Oct 2025 – Jan 2026 data was released as BETA. Absolute levels can be off, and ASF warns that mixing products of different maturity can show differences caused only by processing changes. Compare BETA dates with each other, not with later dates (<a href="https://hyp3-docs.asf.alaska.edu/nisar-docs/availability-overview/" target="_blank" rel="noopener">ASF data availability</a>). "VALIDATED" describes the maturity of the NISAR product. It does not mean our change test has been validated.</li>
<li><b>Gaps.</b> Our set has no acquisitions between Jan 18 and Jun 23, 2026, and NISAR has an instrument data gap from Jul 27 to Aug 10, 2026.</li>
<li><b>Radar brightness is not land use.</b> Wind on water, rain, soil moisture, crop growth and viewing geometry also change backscatter. A coloured pixel means "the surface changed for the radar", not why. Seasonal farm changes are common in both areas.</li>
<li><b>Candidates are not footprints.</b> Hectare figures count pixels that passed the test. They are not measured building or construction areas, and false-positive and missed-detection rates have not been measured.</li>
<li>Faint stripes over the sea at Saemangeum are radar artefacts, not real features.</li>
</ul>
<h3>Open source</h3>
<p>Code, processing scripts and this site: <a href="https://github.com/nodora-lab/nisar-ground-shift" target="_blank" rel="noopener">github.com/nodora-lab/nisar-ground-shift</a> (Apache-2.0). To run it for a new place, add the location to both processing scripts and to <code>web/content.js</code>, then rerun them. You need a free Earthdata Login.</p>
<h3>Use of SI tools</h3>
<p>We used SI assistants (Claude, ChatGPT) to help draft code and English text, and to check facts against public sources. The team reviewed all of it. All radar overlays come from NISAR data through the scripts above.</p>
<p>Team CIELIEN · NASA Space Apps Challenge 2026 · Dancing with the SARs</p>`
};
