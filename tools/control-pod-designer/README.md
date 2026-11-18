# FT412 control-module layout editor

Standalone, offline HTML editor for arranging the project electronics in an enclosure attached outside the left-hand 20×40 profile, viewed from the front. The starting layout is 280 × 120 × 90 mm with an adjustable print split between the Pi and DLC32. The screen mounts on a 45° incline starting at the top of a 30 mm front lip. The first 55 mm are reserved for the display and the incline meets the level roof at 60 mm.

`npm run build` bundles the application, including Three.js and OrbitControls, into identical standalone files at `/tools/control-module/` and `/downloads/ft412-control-module-designer.html`. No CDN, backend, login, analytics, user photos, private tracker data or network connection is required by the editor. Three.js is MIT licensed; its bundled license notices are retained.

The board envelopes, major components and connector paths are schematic. The screen model was identified from its front label. The Pi/MKS/MOSFET PCB sizes use nominal published geometry; the fan, cooler, fuse-holder, switch and screen envelopes remain editable physical-verification tasks. Raspberry Pi's drawing itself states that it is reference geometry rather than production data. Port windows are proposed reservations, not manufacturing-ready connector drawings or electrical pinouts.

## Interaction

- Drag components in plan, front, side or 3D views. Drag empty 3D space to orbit and use the wheel to zoom.
- Edit dimensions, position, mounting face, grouping, rotation and the fan/display aperture in the inspector.
- Pi movement carries the CanaKit heatsink and fan; the fan opening follows their plan position on the flat roof. The MKS moves with both drivers.
- The owner's layout uses one rear cable pass-through next to the switch, a top fan opening and honeycomb ventilation on the profile-facing wall. Connector guides show cable space. The panel openings follow the mounted parts.
- Hide the electronic components to inspect the six internal cable clips and the four floor mounts. Nominal screw sockets follow the Pi, DLC32, MOSFET and fuse-holder cradle. Hexagonal vents leave clearance for the inner-wall clips, the rail supports and the print seam.
- Collision checks use 3D oriented bounding boxes. Only the expected Pi/cooler and MKS/driver parent-to-child envelope overlaps are excluded; fan-to-heatsink and driver-to-driver clashes remain detectable even in linked groups. The editor does not validate PCB sockets, mounting engagement, connector internals or thermal behavior.
- Undo/redo covers layout edits. The browser stores the local design; Export JSON and Save HTML preserve a portable copy.
- JSON import accepts versions 1 and 2. Existing customized layouts keep their geometry. A browser that previously saved only the first stock layout opens the owner's new layout automatically.

The exported `ft412-control-layout` schema contains millimetre units, enclosure dimensions, part poses/envelopes, cutout reservations, print split and mounting stations. `fabricationReady` remains false. A later CAD pass must verify physical hardware, cable paths, screw lengths, attachment loads, print tolerances and cooling before manufacturing.

## Reference geometry

- [Raspberry Pi 5 drawing](https://pip.raspberrypi.com/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf)
- [DLC32 hardware](https://github.com/Macrobase-tech/MKS-DLC32/tree/main/MKS%20DLC32%2BTS24/Hardware)
- [Adafruit 5648 hardware](https://learn.adafruit.com/adafruit-mosfet-driver/downloads)

`tests/control-pod-designer.test.mjs` checks group transforms, mounting planes, 3D intersections, split constraints and JSON round trips. Browser interaction/export checks are recorded privately with the project QA evidence.
