# FT412 control-module layout editor

Standalone, offline HTML editor for arranging the project electronics in an enclosure attached outside the right-hand 20×40 profile. The initial length is 355 mm, with two print sections sized for a nominal 256 mm bed and an adjustable split.

`npm run build` bundles the application, including Three.js and OrbitControls, into identical standalone files at `/tools/control-module/` and `/downloads/ft412-control-module-designer.html`. No CDN, backend, login, analytics, user photos, private tracker data or network connection is required by the editor. Three.js is MIT licensed; its bundled license notices are retained.

The board envelopes, major components and connector paths are schematic. The screen model was identified from its front label. The Pi/MKS/MOSFET PCB sizes use nominal published geometry; the fan, cooler, fuse-holder, switch and screen envelopes remain editable physical-verification tasks. Raspberry Pi's drawing itself states that it is reference geometry rather than production data. Port windows are proposed reservations, not manufacturing-ready connector drawings or electrical pinouts.

## Interaction

- Drag components in plan, front, side or 3D views. Drag empty 3D space to orbit and use the wheel to zoom.
- Edit dimensions, position, mounting face, grouping, rotation and the fan/display aperture in the inspector.
- Pi movement carries its cooler and lid fan in XY; changing the Pi's height retains the fan at the lid. MKS rotation carries its two drivers.
- Collision checks use 3D oriented bounding boxes. Components in one declared assembly family are intentionally excluded from mutual collision checks; the editor does not validate PCB sockets, mounting engagement, connector internals or thermal behavior.
- Undo/redo covers layout edits. The browser stores the local design; Export JSON and Save HTML preserve a portable copy.
- Import JSON validates the schema, bounded numeric values, unique part IDs and non-cyclic grouping. It does not execute imported content.

The exported `ft412-control-layout` schema contains millimetre units, enclosure dimensions, part poses/envelopes, cutout reservations, print split and mounting stations. `fabricationReady` remains false. A later CAD pass must verify physical hardware, cable paths, screw lengths, attachment loads, print tolerances and cooling before manufacturing.

## Reference geometry

- [Raspberry Pi 5 drawing](https://pip.raspberrypi.com/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf)
- [DLC32 hardware](https://github.com/Macrobase-tech/MKS-DLC32/tree/main/MKS%20DLC32%2BTS24/Hardware)
- [Adafruit 5648 hardware](https://learn.adafruit.com/adafruit-mosfet-driver/downloads)

`tests/control-pod-designer.test.mjs` checks group transforms, mounting planes, 3D intersections, split constraints and JSON round trips. Browser interaction/export checks are recorded privately with the project QA evidence.
