# RUST SIGNATURE: Declarations

**Rust Signature: iron-oxide mapping at Noamundi with EO-1 Hyperion**

Sakshi D. Maske · Independent Geospatial Researcher · ORCID [0009-0002-5683-5966](https://orcid.org/0009-0002-5683-5966)

Short case study, rebuilt October 2026 · Code: [github.com/sakshimaske303-commits/RUST_SIGNATURE](https://github.com/sakshimaske303-commits/RUST_SIGNATURE)

## In brief

- One EO-1 Hyperion scene (16 April 2011) over the Noamundi iron-ore mine, Jharkhand, analysed over 25.65 km².
- Bare ground shows a clear absorption trough near 880–900 nm, the shape expected for ferric iron; vegetation shows none.
- 68% of pixels inside the three listed mine working areas fall in the iron-oxide class, against 23% in the rest of the area.
- At 30 m the listed pits cannot be told apart from the surrounding benches and dumps (median band depth 0.048 against 0.049).
- The mine's clearance already requires satellite mapping of the lease; this measure is a public, rerunnable check on the part of that record a satellite can see.
- At India's forest NPV rates the 7.33 km² of bare ground in the window corresponds to Rs 49–117 crore, an order of magnitude rather than a figure for the lease.

## What kind of work this is

This is a short methods case study, not a peer-reviewed paper or a preprint. It uses one date, 30 m pixels and no field or laboratory spectra, so its iron-oxide class means "bare ground with an iron-oxide absorption" and is not a map of ore grade. Because the relative reflectance is computed against the scene mean, and the scene is mostly forest, part of the "deeper than average" signal simply reflects less vegetation (ferric depth and NDVI correlate at r = −0.80).

## Sources and reuse

The Hyperion scene is from the USGS EO-1 archive, accessed through Google Earth Engine (`EO1/HYPERION`). The three working areas are taken from the corner coordinates in the Indian Bureau of Mines inspection report for the mine, and their rectangles are therefore approximate. The exported scene is in the repository, and `python run_all.py` reproduces every number in `outputs/summary.json` and every figure and map.

## Author, funding and interests

I did the whole study alone: the question, the Earth Engine export, the processing, the classification, the check against the mine areas, the figures and the write-up. It received no funding, and I have no competing interests and no link with the mine's operator. Only public satellite imagery, a public government report and the operator's published compliance report are used, so no ethical approval was needed.

## AI assistance

I used Claude (Anthropic), an AI assistant, in a limited way on this case study. It helped me check that the areas, percentages and band depths quoted in the report and on the project page matched `outputs/summary.json`, and it helped me trace the cause when a processing or plotting script did not run. I wrote the original report myself, and asked it to point out sentences that were unclear or too technical, anything that seemed missing, and punctuation; I chose what to change. For the sections added in November 2026 (policy context, forest price and the indicator as a variable), it also helped me find and read the public sources, the mine's clearance compliance report and the 2022 NPV revision, and drafted text that I checked against those sources and edited. The choice of the scene, the band clean-up, the index definitions, the class rules and the reading of the results are my own. I checked everything it suggested and am responsible for the content.
