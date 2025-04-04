# Segmata
------------------------
This software is in link with Vesuvius project (scrollprize.org).
Segmata is a program that allows users to optimize segmentation from Khartes, https://github.com/KhartesViewer/khartes.
For rendering layers it uses: vesuvius-render from https://github.com/jrudolph/vesuvius-gui
It is written in Python.

The main emphasis of Segmata is to automatically perform modifications on .obj file in order to improve the segmentation in terms of:
- Visual rendering of layers
- Inference result on segment (in a future step)

The .obj modifications are done on individual vertex displacements along normals (loop over all vertex). This displacement is limited to XX pixels.
The cost function for deciding is the modified point is better can be based on:
- Maximize bright pixels count (the papyrus layer is brighter than "holes")
- Minimize dark pixel count or dark contours area (decrease "holes" or dark zones in papyrus)

## Workflow

![workflow](images/segmata_workflow.jpg)


## Example
1. Create a simple fragment in Khartes
![khartes](images/khartes_view.jpg)
![origin_image](images/32.jpg_originale.jpg)
2. Launch segmata
Result at first pass:
![first pass result](images/32.jpg_pass1.jpg)
Result at second pass:
![first pass result](images/32.jpg_pass2.jpg)
Result at third pass:
![first pass result](images/32.jpg_pass3.jpg)


## Installation

Required installation: Khartes and vesuvius-render

## Usage

```
segmata
```

