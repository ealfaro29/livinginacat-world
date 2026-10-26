# FDM electronics mount · FT412

CAD prototype, not printed or physically tested. Replace the previous PCB holder with `fdm_pcb_holder_electronics_x1` and add one `fdm_5648_retainer_x1`. Do not print both PCB holders.

The wing faces outside the frame. It carries Adafruit 5648 and NKK S301 with an open-top side/rear low-voltage terminal guard. This is not a closed enclosure or a mains enclosure. Reuse the four DLC32 M3×10 and two frame FHCS M5×12 already counted. Retainer and strain relief use four 4-inch Fermerry ties, with no additional screws.

1. Print the oriented STL in PETG, initially 0.2 mm layers, six walls and 60% gyroid. Inspect wing/panel/guard supports in the slicer. Test fit before installing electronics.
2. Seat the 5648 on four supports. Two Ø2.1 mm locating pins enter Ø2.5 mm holes at 22.86/2.54 and 22.86/15.24 in the official Eagle coordinates. PCB underside is 2 mm above the platform.
3. The retainer contacts only two bare mounting ears. Use two ties around outer posts/slots, never over components. Two other ties strain-relieve the JST cable and switch harness. Trim tails with the kit’s cutters.
4. Mount S301 in the 3 mm panel, Ø12.7 mm hole and Ø3.2 anti-rotation feature 9 mm from center. Use supplied nuts/washers and an adjustable wrench. Hold the rear nut without rotating the switch body. Do not apply a metal-panel datasheet maximum torque to PETG; check for crushing and loosening.
5. Solder unpowered. Insulate each 6 mm tab separately with the included electrical tape. The kit’s heat-shrink has not been confirmed to fit over those tabs. The guard does not replace insulation.
6. Keep connectors, microSD and tie slots clear. Verify polarity, insulation, continuity, 12 V cutoff and strain relief before energizing. No exposed copper may contact the profiles or board.

CAD checks: each part is a valid solid and closed, consistently oriented, single-component STL at Z0; STEP/STL volume comparison below 0.2%. Eight intersection checks report zero volume: DLC32/mount, 5648/mount, 5648/retainer, components/retainer, mount/retainer, S301/mount, bushing/panel and S301/5648. DLC32 placements are applied to child solids to avoid compound-transform errors. See `qa/electronics.json`. These results do not validate wiring or physical fit.
