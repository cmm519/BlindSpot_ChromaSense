# Enhancement method evaluation

## Selected method

**Lightness separation** is the one method that ChromaSense ships (SRS-FR-029). It has the highest reduction in confusable pairs.

## Dataset

The dataset is `src/color_engine/tests/data/flat_graphics/`: 29 generated flat graphics (bars, pies, map shapes, and geometric shapes), with their colors in `labels.json`.

Each graphic was run under protan, deutan, tritan, and achromatopsia at severity 1, with a confusion threshold of CIEDE2000 10. The palette was extracted again from each enhanced image before pairs were counted again, which is the same re-detection that the upload pipeline runs.

## Results

| Method | Pairs before | Pairs after | Reduction | Mean CIEDE2000 change in the mask | Pixels changed outside the mask |
| --- | --- | --- | --- | --- | --- |
| Lightness separation | 77 | 4 | 94.8 percent | 9.3 | 0 |
| Targeted daltonization | 77 | 31 | 59.7 percent | 11.6 | 0 |
| Hue rotation | 77 | 43 | 44.2 percent | 24.7 | 0 |

Before and after pair counts for lightness separation, by CVD type:

| CVD type | Pairs before | Pairs after |
| --- | --- | --- |
| Protan | 10 | 1 |
| Deutan | 22 | 1 |
| Tritan | 5 | 0 |
| Achromatopsia | 40 | 2 |

## Selection rule

The method with the highest percent reduction in confusable pairs is selected. A tie would go to the smallest mean CIEDE2000 change inside the mask. There was no tie.

## Method details

- **Lightness separation**: spaces the colors of each confusable group 22 CIELAB lightness units apart, between 15 and 90. It avoids the lightness of other colors first, and then moves each color as little as possible. A lightness gap survives every simulated CVD type, including achromatopsia. It also needs no CVD profile, which matches the `enhance_9` signature.
- **Targeted daltonization**: added the simulation error to the green and blue channels with the Fidaner matrix, inside the mask.
- **Hue rotation**: rotated CIELAB hue by up to 60 degrees in each direction across each group.

The rejected methods were simple forms of each technique, written as temporary code outside the repository. A more elaborate daltonization or hue rotation could score higher. Under achromatopsia, which keeps only luminance, they removed fewer pairs (40 before; 22 and 32 after) than lightness separation (2 after).
