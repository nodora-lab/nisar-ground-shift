// Text content for Ground Shift. SI note: English text drafted with SI assistance (Claude, ChatGPT) and reviewed by the team.
window.CONTENT = {
  gaps: [
    { from: "2026-01-20", to: "2026-06-17", short: "no public data", label: "No NISAR data released between the BETA set (to Jan 20, 2026) and the PROVISIONAL set (from Jun 17, 2026)" },
    { from: "2026-07-27", to: "2026-08-10", short: "instrument gap", label: "Permanent NISAR instrument data gap, Jul 27 – Aug 10, 2026" }
  ],
  sites: {
    saemangeum: {
      chip: "Saemangeum · tidal flats", color: "var(--teal)",
      short: "Tidal flats → reclaimed land, roads and ports",
      kicker: "STUDY AREA 1 OF 2",
      title: "Saemangeum: a tidal flat becoming land",
      meta: "West coast of Korea · 35.8°N, 126.6°E · NISAR descending track 133, frame 70",
      signals: [
        ["var(--up)", "Brighter in HH", "New embankments, roads and buildings bounce the radar straight back (double bounce)."],
        ["var(--down)", "Darker", "Open water and freshly flattened, smooth sand reflect the signal away from the satellite."],
        ["var(--prov)", "HV changes", "Cross-polarised (HV) signal rises with vegetation and rough fill, and falls when land is scraped bare."]
      ],
      why: "Tidal flats are nurseries for fish and resting places for migratory birds. Radar lets anyone follow how fast they turn into land, in any weather."
    },
    yongin: {
      chip: "Yongin · farmland → chip fabs", color: "var(--up)",
      short: "Farmland and hills → semiconductor cluster",
      kicker: "STUDY AREA 2 OF 2",
      title: "Yongin: farmland making way for chip factories",
      meta: "South of Seoul · 37.1°N, 127.3°E · same NISAR track and dates",
      signals: [
        ["var(--up)", "Brighter in HH", "Steel frames and concrete walls create strong double-bounce returns."],
        ["var(--down)", "Darker", "Graded, compacted ground is smoother than fields and forest."],
        ["var(--prov)", "HV drops", "Trees and crops are removed, so there is less volume scattering."]
      ],
      why: "Large industrial sites change land, water and traffic for whole towns. A free, repeatable radar view helps residents and planners see the pace of change."
    }
  },
  legend: {
    rgb: { title: "RGB COMPOSITE", items: [["#ff5a5a", "Red = HH (surface, buildings)"], ["#5aff8a", "Green = HV (vegetation, rough volume)"], ["#5a8aff", "Blue = HH ÷ HV (smooth vs. rough)"]] },
    hh: { title: "HH BACKSCATTER", items: [["linear-gradient(90deg,#000,#fff)", "−24 dB → +2 dB"]] },
    hv: { title: "HV BACKSCATTER", items: [["linear-gradient(90deg,#000,#fff)", "−32 dB → −8 dB"]] },
    chg: { title: "HH CHANGE VS. FIRST DATE", items: [["#FF9F43", "Brighter by ≥ 2 dB (new structures, bare soil)"], ["#4DA3FF", "Darker by ≥ 2 dB (water, smooth fill)"]] }
  },
  method: `<h2>Data &amp; method</h2><p>Everything on this site is computed from free NISAR radar data. No SI-generated imagery is used in the map views.</p><p><i>(Full method text is written after the data is processed.)</i></p>`
};
