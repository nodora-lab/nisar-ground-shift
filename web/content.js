// Text content for Ground Shift. SI note: English text drafted with SI assistance (Claude, ChatGPT) and reviewed by the team.
window.CONTENT = {
  gaps: [
    { from: "2026-01-20", to: "2026-06-17", short: "no public data", label: "No NISAR data released between the BETA set (to Jan 20, 2026) and the PROVISIONAL set (from Jun 17, 2026)" },
    { from: "2026-07-27", to: "2026-08-10", short: "instrument gap", label: "Permanent NISAR instrument data gap, Jul 27 – Aug 10, 2026" }
  ],
  sites: {
    saemangeum: {
      chip: "Saemangeum", color: "var(--teal)",
      short: "Tidal flats → reclaimed land, roads and ports",
      kicker: "STUDY AREA 1 OF 2",
      finding: "Radar finding: about {ha} ha of new strong reflectors appeared in {n} spots between summer and autumn 2026, mostly on reclaimed land inside the sea wall and in the northern industrial area.",
      title: "Saemangeum: a tidal flat becoming land",
      meta: "West coast of Korea · 35.8°N, 126.6°E · NISAR descending track 133, frame 70",
      signals: [
        ["var(--up)", "Brighter in HH", "New embankments, roads and buildings bounce the radar straight back (double bounce)."],
        ["var(--down)", "Darker", "Open water and freshly flattened, smooth sand reflect the signal away from the satellite."],
        ["var(--prov)", "HV changes", "Cross-polarised (HV) signal rises with vegetation and rough fill, and falls when land is scraped bare."]
      ],
      why: "Saemangeum was a major feeding and resting site for migratory shorebirds on the East Asian–Australasian Flyway, and their numbers fell sharply after the sea wall closed. The land is still being built today. Radar sees through clouds and works at night, so anyone can follow how fast the flats turn into land.",
      facts: [
        ["The 33.9 km sea wall closed in 2006 and was completed in 2010. Before that, the area was tidal flats and the estuaries of the Mangyeong and Dongjin rivers.", "https://saemangeum.go.kr/sda/en/content.do?key=2010214151548", "Saemangeum Development Agency"],
        ["Great Knots and Spoon-billed Sandpipers were among the shorebirds that declined after closure.", "https://doi.org/10.1071/MU16006", "Emu (2016)"],
        ["2026 work plan: industrial-land reclamation, a regional connecting road, and the new port, where two berths are complete.", "https://www.saemangeum.go.kr/sda/brd/view.do?key=2009074409621&nttSn=10702", "Agency 2026 plan"],
        ["A revised master plan (Oct 28, 2026) sets 169.6 km² for reclamation and development by 2035.", "https://www.opm.go.kr/opm/news/press-release.do?articleNo=163983&mode=view", "Prime Minister's Office"]
      ]
    },
    yongin: {
      chip: "Yongin", color: "var(--up)",
      short: "Farmland and hills → semiconductor cluster",
      kicker: "STUDY AREA 2 OF 2",
      finding: "Radar finding: the largest new-structure spots our method found, with no location hints, fall on the SK hynix cluster site in Wonsam-myeon, and one falls inside the national complex area near Namsa-eup, where site preparation began on Oct 28, 2026.",
      title: "Yongin: farmland making way for chip factories",
      meta: "South of Seoul · 37.1°N, 127.3°E · same NISAR track and dates",
      signals: [
        ["var(--up)", "Brighter in HH", "Steel frames and concrete walls create strong double-bounce returns."],
        ["var(--down)", "Darker", "Graded, compacted ground is smoother than fields and forest."],
        ["var(--prov)", "HV drops", "Trees and crops are removed, so there is less volume scattering."]
      ],
      why: "Two chip clusters are being built here at once, and together they cover about 12 km² of hills, forest and farmland. Projects this large change land, water and traffic for whole towns. A free, repeatable radar view helps residents and planners see the pace of change for themselves.",
      facts: [
        ["SK hynix cluster, Wonsam-myeon: about 4.15 million m². Site work began in Apr 2022 and the first fab in Feb 2025.", "https://news.skhynix.com/en/sk-hynix-board-approves-yongin-semiconductor-cluster-plan/", "SK hynix"],
        ["Its first cleanroom is targeted for Feb 2027.", "https://news.skhynix.com/en/new-facility-investment-for-yongin-semiconductor-cluster/", "SK hynix"],
        ["National semiconductor complex, Idong-eup / Namsa-eup: about 7.78 million m², planned for six fabs.", "https://www.yna.co.kr/view/AKR20260901049800003", "Yonhap"],
        ["Land compensation began on Dec 22, 2025. First-stage site preparation started on Oct 28, 2026, five days before our latest radar date.", "https://council.yongin.go.kr/viewer/minutes.do?mem_sch=all&schwrd=&uid=8917", "Yongin City Council"]
      ]
    }
  },
  legend: {
    rgb: { title: "RGB COMPOSITE", items: [["#ff5a5a", "Red = HH (surface, buildings)"], ["#5aff8a", "Green = HV (vegetation, rough volume)"], ["#5a8aff", "Blue = HH ÷ HV (smooth vs. rough)"]] },
    hh: { title: "HH BACKSCATTER", items: [["linear-gradient(90deg,#000,#fff)", "−24 dB → +2 dB"]] },
    hv: { title: "HV BACKSCATTER", items: [["linear-gradient(90deg,#000,#fff)", "−32 dB → −8 dB"]] },
    new: { title: "NEW BUILT · JUN–JUL → OCT–NOV 2026", items: [["#FF9F43", "Dim on all 3 summer dates (≤ −8 dB HH), bright on all 3 autumn dates (≥ −3 dB). Total ≈ {ha} ha in {n} spots — click a circle."], ["transparent", "Strict on purpose: crops and wind rarely pass both tests."]] },
    chg: { title: "HH CHANGE VS. JUN 23, 2026 (FIRST CALIBRATED DATE)", items: [["#FF9F43", "Brighter by ≥ 2 dB (new structures, bare soil)"], ["#4DA3FF", "Darker by ≥ 2 dB (water, smooth fill)"]] }
  },
  method: `<h2>Data &amp; method</h2>
<p>Every map image on this site is computed from free NISAR radar data. No SI-generated imagery is used in the map views.</p>
<h3>Data</h3>
<table>
<tr><th>Product</th><td>NISAR Level-2 GCOV (Geocoded Polarimetric Covariance), L-band, frequency A, HH and HV backscatter</td></tr>
<tr><th>Archive</th><td><a href="https://search.asf.alaska.edu/" target="_blank" rel="noopener">NASA Alaska Satellite Facility DAAC</a>, collections NISAR_L2_GCOV_BETA_V1, NISAR_L2_GCOV_PROVISIONAL_V1, NISAR_L2_GCOV_V1</td></tr>
<tr><th>Geometry</th><td>Descending track 133, frame 70 — one radar scene covers both study areas</td></tr>
<tr><th>Dates</th><td>18 acquisitions, Oct 26, 2025 – Nov 2, 2026 (12-day repeat when data is available)</td></tr>
<tr><th>Basemap</th><td>Esri World Dark Gray Canvas (© Esri, HERE, Garmin, © OpenStreetMap contributors), labels and background only</td></tr>
</table>
<h3>Processing</h3>
<ol>
<li><b>Read only what we need.</b> Each GCOV file is about 6 GB. We open it over HTTPS with Earthdata Login and read only the HDF5 chunks inside each study area (<code>scripts/01_subset_gcov.py</code>).</li>
<li><b>Reduce speckle.</b> 5 × 5 moving-average filter on linear backscatter, in the product's native map grid.</li>
<li><b>Put every date on one grid.</b> Reproject to latitude/longitude at 0.00025° (about 25 m) and convert to decibels (<code>scripts/02_render.py</code>).</li>
<li><b>Colour.</b> RGB = HH (−24 to +2 dB), HV (−30 to −6 dB), HH − HV (0 to 18 dB). The same fixed stretch is used for every date so colours can be compared over time.</li>
<li><b>Change.</b> HH on each date minus HH on Jun 23, 2026, the first calibrated (PROVISIONAL) date. Only differences of 2 dB or more are coloured; the colour gets stronger up to 10 dB.</li>
<li><b>Trend chart.</b> Median HH and HV (dB) over the whole study area on each date.</li>
</ol>
<h3>Limits — please read before drawing conclusions</h3>
<ul>
<li><b>BETA dates are not calibrated.</b> Oct 2025 – Jan 2026 data was released as BETA. Absolute levels can be off, and ASF warns that mixing BETA and PROVISIONAL products can show differences caused only by processing changes. Compare BETA dates with each other, not with later dates (<a href="https://hyp3-docs.asf.alaska.edu/nisar-docs/availability-overview/" target="_blank" rel="noopener">ASF data availability</a>).</li>
<li><b>Gaps.</b> No public data between Jan 20 and Jun 17, 2026, and a permanent instrument gap from Jul 27 to Aug 10, 2026.</li>
<li><b>Radar brightness is not land use.</b> Wind on water, rain, soil moisture and crop growth also change backscatter. A coloured pixel says "the surface changed for the radar", not why. Seasonal farm changes are common in both areas.</li>
<li><b>Speckle and resolution.</b> After filtering and resampling, features smaller than about 50 m are not reliable.</li>
<li>Faint stripes over the sea at Saemangeum are radar artefacts, not real features.</li>
</ul>
<h3>Open source</h3>
<p>Code, processing scripts and this site: <a href="https://github.com/nodora-lab/nisar-ground-shift" target="_blank" rel="noopener">github.com/nodora-lab/nisar-ground-shift</a> (Apache-2.0). Anyone with a free Earthdata Login can rerun it for a new place by changing one bounding box.</p>
<h3>Use of SI tools</h3>
<p>We used SI assistants (Claude, ChatGPT) to help draft code and English text, and to check facts. The team reviewed all of it. All map images come from NISAR data through the scripts above.</p>
<p>Team CIELIEN · NASA Space Apps Challenge 2026 · Dancing with the SARs</p>`
};
