# Project Report

## Rust Signature: Spectral Discrimination of Mine Tailings and Waste Rock at Noamundi Using EO-1 Hyperion

### Overview

This case study uses an EO-1 Hyperion hyperspectral scene over the Noamundi iron ore mine (West Singhbhum, Jharkhand) to spectrally separate iron-oxide-rich waste rock and tailings from vegetated fringe and mixed bare surface, using continuum-removed diagnostic absorption features rather than simple band ratios. Hyperion's 220+ narrow spectral bands can resolve mineralogically specific absorption troughs — a ferric-iron feature centered near 870nm and an Al/Fe-OH clay feature near 2200nm — that collapse into a handful of broad, indistinguishable bands on multispectral sensors like Landsat or Sentinel-2. That resolution is the entire reason to reach for hyperspectral data here instead of the multispectral imagery used throughout the rest of this portfolio.

Hyperspectral work at Noamundi and the surrounding Kiriburu–Meghahataburu/Bailadila iron ore belt splits into two threads right now, and nobody's merged them. One maps ore grade and mineral chemistry directly — spectral unmixing to evaluate iron ore grades, characterizing hematite mineral classes. The other tracks what the mining belt is doing to the surrounding Saranda forest — canopy health and tree-species diversity, using the same sensor. Neither one has actually spectrally characterized the tailings, waste-rock dumps, or mine-associated water bodies sitting physically between these two studied surfaces — even though the same sensor type has been used for exactly this purpose elsewhere: Hyperion and HyMap data mapped pyrite mine waste and acid-mine-drainage-affected water in the Iberian Pyrite Belt, Spain, using this same class of continuum-removed absorption analysis. I want to be upfront about scope here — this is a case-study/map-making project, not a full research paper. The goal is a defensible, portfolio-ready spectral map that fills one specific, citable gap, not a publication-length study.

### Objectives

1. Confirm Hyperion archive coverage of Noamundi via Google Earth Engine's `EO1/HYPERION` collection and export a clipped, quality-checked scene for analysis — I didn't want to assume a published acquisition was still retrievable and find out halfway through.
2. Build my own signal-based bad-band mask (water-vapor absorption windows, low-SNR bands) instead of copying a hardcoded band list from a paper, and check the wavelength assignment against Hyperion's known VNIR/SWIR instrument seam and atmospheric absorption structure.
3. Compute continuum-removed diagnostic absorption indices — a ferric-iron band depth (~870nm) and an Al/Fe-OH band depth (~2200nm) — instead of simple two-band ratios, so the indices actually isolate mineralogically diagnostic features and aren't just a generic brightness proxy.
4. Run unsupervised classification on shape-normalized (per-pixel) spectra so surface material composition gets separated from topographic/illumination brightness, then cross-check the resulting classes against an independently built true-color/false-color browse composite of the same scene.
5. Produce a labeled surface classification distinguishing iron-oxide waste rock/tailings, vegetated/forest fringe, and mixed bare surface — and flag openly where mine-water bodies couldn't be confidently separated at this resolution, instead of claiming a class the data can't actually support.
6. Package the result as a portfolio-ready interactive map (satellite basemap, classed legend) that addresses the specific gap at this site: nobody had spectrally characterized the tailings, waste-rock, and mine-water surfaces here before.

### Related Work & Citations

Hyperspectral work at Noamundi and the neighboring Kiriburu–Meghahataburu/Bailadila iron ore belt falls into two established threads. The first maps ore grade and mineral chemistry directly — linear spectral unmixing of Hyperion data to estimate iron ore grades at Noamundi (Magendran & Sanjeevi), a companion spectral-unmixing study at Kiriburu and Meghahataburu, and hematite ore-class characterization at Bailadila (Shaik et al., 2021). The second tracks the mining belt's effect on the surrounding Saranda forest — canopy health and tree-species diversity assessed with Hyperion and Landsat data (Kayet et al., 2020). Neither thread has spectrally characterized the tailings, waste-rock dumps, or mine-associated water bodies that sit physically between these two studied surfaces, despite the same sensor type being used for exactly this purpose elsewhere: Hyperion and HyMap data were used to map pyrite mine waste and acid-mine-drainage-affected water in the Iberian Pyrite Belt, Spain, using the same class of continuum-removed absorption-feature analysis applied here (Riaza et al., 2012).

**References**

1. Riaza, A., Buzzi, J., García-Meléndez, E., Vázquez, I., Bellido, E., Carrère, V., & Müller, A. (2012). Pyrite mine waste and water mapping using Hymap and Hyperion hyperspectral data. *Environmental Earth Sciences*, 66(7), 1957–1971. https://doi.org/10.1007/s12665-011-1422-0
2. Shaik, I., Begum, S. K., Nagamani, P. V., & Kayet, N. (2021). Characterization and mapping of hematite ore mineral classes using hyperspectral remote sensing technique: a case study from Bailadila iron ore mining region. *SN Applied Sciences*, 3, Article 182. https://doi.org/10.1007/s42452-021-04213-3
3. Kayet, N., Pathak, K., Chakrabarty, A., Kumar, S., Singh, C. P., & Chowdary, V. M. (2020). Assessment of mining activities on tree species and its diversity in hilltop mining areas using Hyperion and Landsat data. *Environmental Science and Pollution Research*, 27(34), 42750–42766. https://doi.org/10.1007/s11356-020-09795-w
4. Magendran, T., & Sanjeevi, S. Hyperion image analysis and linear spectral unmixing to evaluate the grades of iron ores in parts of Noamundi, Eastern India. *International Journal of Applied Earth Observation and Geoinformation*. (Indexed via ScienceDirect, PII S0303-2434(13)00103-7 — confirm exact volume/page before final citation formatting.)
5. Hyperspectral Image Analysis for Iron Mineral Exploration and Spectral Unmixing Study in Kiriburu and Meghahataburu Mining Areas, West Singbhum, Jharkhand. (Indexed via ResearchGate — confirm exact author order/volume/page before final citation formatting.)

---

# Development Log

**Data & tools:** EO-1 Hyperion (NASA/USGS), scene 16 Apr 2011, WRS Path/Row 140/45, sourced via Google Earth Engine's `EO1/HYPERION` collection; Python (rasterio, scikit-learn, matplotlib) for the analysis; Folium for the final interactive map.

**Step 1 — First I had to check the scene actually exists.**
Two published papers already pointed at Noamundi as a confirmed Hyperion site, but I wasn't going to build a whole case study on a scene I hadn't pulled myself. Wrote a short script against `EO1/HYPERION`, filtered to Noamundi's coordinates and the 16 April 2011 window, ran it in the Earth Engine Code Editor. One scene came back. That's what let me actually start the day — if it had come back empty, Bailadila was the backup site.

**Step 2 — Export and first look.**
Clipped a 3km buffer around the mine point, exported to Drive as a GeoTIFF, pulled it down locally. 198 bands, 30m pixels, roughly a 6km box. First thing I checked wasn't the spectral content, it was whether the export was even real data and not an empty or corrupt file. It was fine — every band had a sensible dynamic range.

**Step 3 — Band quality, done properly instead of guessing.**
I could have just pasted in a bad-band list I half-remembered from some paper. Didn't do that. Computed the per-band mean signal myself and flagged anything sitting inside Hyperion's known water-vapor absorption windows (~1350–1490nm, ~1780–1970nm), plus anything in the bottom signal percentile. 35 of 198 bands got dropped this way. Plotted the surviving mean spectrum afterward and it had exactly the shape a real Hyperion radiance curve should — the VNIR/SWIR instrument seam dip around 900nm, both water-vapor troughs sitting right where I'd flagged them. That match is what actually convinced me the data was clean before I touched any indices.

**Step 4 — The clustering mistake that almost went into the final map.**
First K-means pass on the cleaned bands looked fine at a glance — six clusters, clean-looking split. Then I plotted each cluster's mean spectrum and realized all six were the same curve at six different brightness levels. I'd normalized each band's range across the image, but never removed each pixel's own overall brightness — so the model was clustering by how sunlit a patch of ground happened to be, not by what it was actually made of. Classic shadow/topography contamination, not a real material signal. Fixed it by dividing each pixel's spectrum by its own mean before clustering, which strips illumination out and leaves only spectral shape. Re-ran it and this time the clusters actually separated on the indices, not on brightness.

**Step 5 — Getting the iron index right.**
First attempt at an iron-oxide index was the obvious two-band ratio (NIR/red) — what most people reach for first, and what I reached for first too. Problem is that's not how the ferric-iron absorption feature actually behaves. It's a trough centered around 860–900nm, not something a two-point ratio can capture properly. Redid it as a continuum-removed band depth, the same way I was already handling the 2200nm clay/jarosite feature. That version is what made it into the final classification.

**Step 6 — Checking the classification against something real.**
Before I trusted the classified map, I built a true-color and false-color browse composite from the same data and put it side by side with the classification. The dark branching drainage channel visible in the true-color image lines up almost exactly with the "vegetated" class the classification came up with — I never told K-means about that channel, it fell out of the spectral shape completely on its own. That's the kind of agreement that makes a result actually trustworthy, not just plausible-looking.

**Step 7 — What I chose not to force.**
The water index came back too flat across all six clusters to confidently call any of them "mine water." No atmospheric correction, 30m pixels, and the settling ponds here are probably sub-pixel anyway. I could have just picked the lowest-water-index cluster and labeled it water — didn't do that. Left it as an open flag in the map's own legend instead. A map that admits what it couldn't resolve is worth more to me than one that pretends it resolved something it didn't.

**Step 8 — Where this actually lands.**
Iron-oxide waste rock/tailings came out to roughly 18 sq km of the AOI, vegetated fringe about 4.7 sq km, mixed bare surface about 5.5 sq km. That number is the whole point of this case study — the Hyperion literature at this exact site has mapped ore grade, and separately mapped forest health, but nobody had actually put a number on how much of the ground here is spectrally waste rock versus something else. Now there is one.
