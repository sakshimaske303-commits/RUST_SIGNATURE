# Project Report

## Rust Signature: Spectral Discrimination of Mine Tailings and Waste Rock at Noamundi Using EO-1 Hyperion

### Overview

This case study uses an EO-1 Hyperion hyperspectral scene over the Noamundi iron ore mine (West Singhbhum, Jharkhand) to spectrally separate iron-oxide-rich waste rock and tailings from vegetated fringe and mixed bare surface, using continuum-removed diagnostic absorption features rather than simple band ratios. Hyperion's 220+ narrow spectral bands can resolve mineralogically specific absorption troughs — a ferric-iron feature centered near 870nm and an Al/Fe-OH clay feature near 2200nm — that collapse into a handful of broad, indistinguishable bands on multispectral sensors like Landsat or Sentinel-2. That resolution is the entire reason to reach for hyperspectral data here instead of the multispectral imagery used throughout the rest of this portfolio.

Hyperspectral work at Noamundi and the surrounding Kiriburu–Meghahataburu/Bailadila iron ore belt currently splits into two threads that have never been merged. One maps ore grade and mineral chemistry directly, using spectral unmixing to evaluate iron ore grades and characterize hematite mineral classes. The other tracks the mining belt's effect on the surrounding Saranda forest — canopy health and tree-species diversity assessed with the same sensor. Neither thread has spectrally characterized the tailings, waste-rock dumps, or mine-associated water bodies that physically sit between these two studied surfaces, despite the same sensor type being used for exactly this purpose elsewhere — Hyperion and HyMap data were used to map pyrite mine waste and acid-mine-drainage-affected water in the Iberian Pyrite Belt, Spain, using the same class of continuum-removed absorption analysis applied in this case study. This is a case-study/map-making scope, not a full comprehensive research project — the goal is a defensible, portfolio-ready spectral map that fills a specific, citable gap, not a publication-length study.

### Objectives

1. Confirm Hyperion archive coverage of Noamundi via Google Earth Engine's `EO1/HYPERION` collection and export a clipped, quality-checked scene for analysis, rather than assuming a published acquisition is still retrievable.
2. Establish an automatic, signal-based bad-band mask (water-vapor absorption windows, low-SNR bands) instead of relying on a hardcoded literature band list, and validate the wavelength assignment against Hyperion's known VNIR/SWIR instrument seam and atmospheric absorption structure.
3. Compute continuum-removed diagnostic absorption indices — a ferric-iron band depth (~870nm) and an Al/Fe-OH band depth (~2200nm) — rather than simple two-band ratios, to correctly isolate mineralogically diagnostic features instead of a generic brightness proxy.
4. Run unsupervised classification on shape-normalized (per-pixel) spectra to separate surface material composition from topographic/illumination brightness, and cross-validate the resulting classes against an independently built true-color/false-color browse composite of the same scene.
5. Produce a labeled surface classification distinguishing iron-oxide waste rock/tailings, vegetated/forest fringe, and mixed bare surface — explicitly flagging where mine-water bodies could not be confidently separated at this resolution, rather than overclaiming a class the data doesn't support.
6. Package the result as a portfolio-ready interactive map (satellite basemap, classed legend) addressing the specific literature gap at this site: spectral characterization of tailings, waste-rock, and mine-water surfaces.

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

**Step 1 — Confirming the scene actually exists before committing to the site.**
I already had two published papers pointing at Noamundi as a confirmed Hyperion acquisition site, but I didn't want to build a whole case study around a scene I hadn't verified I could actually pull myself. I wrote a short script against `EO1/HYPERION` filtered to Noamundi's coordinates and the 16 April 2011 window and ran it straight in the Earth Engine Code Editor — one scene came back. That single confirmation is what unblocked the rest of the day; if it had returned zero, the fallback was Bailadila.

**Step 2 — Export and first look.**
Clipped a 3km buffer around the mine point, exported the scene to Drive as a GeoTIFF, then pulled it down locally. 198 bands, 30m pixels, roughly a 6km box. The first check wasn't spectral content — it was whether the file was even real data or an empty/corrupt export. It wasn't; every band had a sensible dynamic range.

**Step 3 — Band quality, the honest way.**
Rather than pasting in a bad-band list half-remembered from a paper, I computed per-band mean signal and flagged anything sitting inside Hyperion's known water-vapor absorption windows (~1350–1490nm, ~1780–1970nm) or in the bottom signal percentile. 35 of 198 bands got dropped this way. Plotting the surviving mean spectrum, it had exactly the shape a real Hyperion radiance curve should have — the VNIR/SWIR instrument seam dip around 900nm, the two water-vapor troughs sitting right where they'd been flagged. That match gave real confidence the data was clean before touching any indices.

**Step 4 — The clustering mistake almost shipped.**
The first K-means pass on the cleaned bands looked like it worked — six clusters, clean split — until plotting each cluster's mean spectrum and realizing all six were just the same curve at six different brightness levels. Each band's range had been normalized across the image, but each pixel's own overall brightness was never removed, so the model was clustering by how sunlit a patch of ground happened to be, not by what it was made of — classic topography/shadow contamination, not material signal. Fixed it by dividing each pixel's spectrum by its own mean before clustering, which strips out illumination and leaves only spectral shape. Re-ran it and the clusters actually separated on the indices that time.

**Step 5 — Getting the iron index right.**
The first pass at an iron-oxide index was a simple two-band ratio (NIR/red) — the version most people reach for first. That's not actually how the ferric-iron absorption feature behaves; it's a trough centered around 860–900nm, not a two-point ratio, so it was redone as a continuum-removed band depth the same way the 2200nm clay/jarosite feature was already being handled. That's the version that made it into the final classification.

**Step 6 — Checking the classification against something real.**
Before trusting the classified map, I built a true-color and false-color browse composite from the same cube and laid it next to the classification. The dark branching drainage channel visible in the true-color image lines up almost exactly with the "vegetated" class in the classification — not something K-means was told to do, it fell out of the spectral shape on its own, which is the kind of agreement that makes a result trustworthy.

**Step 7 — What I didn't force.**
The water index came back too flat across all six clusters to confidently call any of them "mine water" — no atmospheric correction, 30m pixels, and settling ponds are probably sub-pixel here anyway. Rather than picking the lowest-water-index cluster and labeling it water, it stays an open flag in the map's own legend. A map that's honest about what it didn't resolve is worth more than one that overclaims a class the data can't actually back up.

**Step 8 — Where this sits.**
Iron-oxide waste rock/tailings came out to roughly 18 sq km of the AOI, vegetated fringe ~4.7 sq km, mixed bare surface ~5.5 sq km. That's the number that matters for the gap this case study fills — the Hyperion literature at this exact site has mapped ore grade and it's mapped forest health, but nobody's put a number on how much of the ground here is spectrally waste rock versus something else.
