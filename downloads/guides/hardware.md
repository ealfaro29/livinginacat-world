# DIY iPhone robot · FramingTech 355/250 + Adafruit 412

FDM prototype derived from PhysiClaw hardware v0.51, commit `8f610d48642aef7d974d3ce09d28e14a4a99bbae`. This variant uses cut profiles without machining, printed motor mounts and a modified touch head. **CAD and meshes have been checked digitally; nothing has been printed, assembled or physically tested.** Files are a prototype starting point, not certification of strength, fit or touch performance.

Read `PUBLIC-RELEASE.md` first. Print only final files in `stl/` with quantities from `qa/print-manifest.json`. `qa/base-generation.json` describes an intermediate PCB holder superseded by the electronics holder. The public release excludes commercial/reference folders and regeneration scripts. Do not mix this variant with the earlier MISUMI/ELECALL design.

## Selected configuration

| Component | Quantity and specification |
|---|---|
| Long profiles | 2 FramingTech 20×40-05, 355 mm |
| Short frame profiles | 2 FramingTech 20×40-05, 190 mm |
| Moving X beam | 1 FramingTech 10×20-05, 185 mm |
| Bed crossmembers | 2 FramingTech 10×20-05, 190 mm |
| Brackets | 8 GS20-05W kits, each with 2 M4×8 screws and 2 SQN05M4 nuts |
| Y guidance | 2 generic MGN9 rails, 250 mm, each with MGN9H carriage |
| X guidance | 1 generic MGN9 rail, 150 mm, with MGN9H carriage |
| M3 T-nuts | 38 RN05BM3: up to 34 rail + 4 bed fasteners |
| M5 T-nuts | 20 RN05BM5; allocation below |
| Actuator | Adafruit 412, 12 V / 0.3 A, 14×17×29.7 mm body; 4.9 mm drawing stroke |
| Tip | Micro Traders B0DSVSVSZN, Ø8.9×4.5 mm metal collar, Ø7 mm mesh |
| Remaining metal plates | 2 rear-idler braces from the purchased 40×18 mm joining plate pack; thickness and fit to be verified |

Profiles are metric 10×20 and 20×40, not imperial 1010/1020. The FramingTech STEP slot opening is at least 5.15 mm. Earlier MISUMI slot-6 nuts are not used. Amazon square M3/M4/M5 nuts fit printed pockets and do not automatically replace FramingTech T-nuts.

Eight gussets replace original end drilling and corner plates: four at the inner frame corners within the lower 20 mm cell, four connecting bed crossmembers to the inner faces of the long profiles. Use `qa/framingtech-frame.json` for bed-top elevation. Square the frame before tightening. This variant does not require profile drilling or tapping.

## Printing

STL units are millimeters at 100% scale, with the selected orientation and minimum Z=0. Do not globally scale parts to compensate for fit. The main bed is 175 mm; verify printable space and slicer margins. Exact bounding boxes are in the manifest.

Initial prototype settings: dry PETG, 0.4 mm nozzle, 0.2 mm layers, 6 perimeters, 6 top/bottom layers, 50–80% infill. Use 80% or near-solid modifiers at motor mounts and screw areas. Use filament/printer manufacturer temperature and cooling guidance. PETG is not PA12; original-design validation does not transfer to home-printed parts.

Print all three coupons and both 412 coupler halves first. Check actual screws/nuts, head recesses, tip and cap diameters. Original pockets have 0.2 mm added clearance; countersunk M3/M5 mouths are Ø7/Ø11.5 mm for selected ISO10642 maxima. XY locating features are reduced to 4.8 mm for the FramingTech slot.

Inspect all slicer layers. Add removable local supports where cavity roofs, head recesses or undercuts require them; remove completely. The 412 cradle rests on the back of its wall, clamp bars on their outside faces, coupler halves with cavities up. Motor mounts rest on their outside faces and retain 3 mm screw seats. Avoid supports in inaccessible passages. Add a 6–8 mm brim to the tall narrow tube bracket.

Four feet are Ø24×22 mm cylinders with 1 mm EVA on the bottom. Their 4 M5×16 screws and 4 RN05BM5 nuts are already counted. A 10.5 mm roof leaves 5.5 mm screw penetration and nominal 0.85 mm slot-bottom clearance. These replace purchased feet; do not fit both.

## Motors and shoulder axles

Two printed mounts replace metal motor plates and motor spacers. A has 8 mm legs and uses 2 M5×16; B has 12 mm legs and uses 2 M5×20. Each motor uses 4 M3×6. Keep original pulley gaps A=0 mm and B=5 mm. See `MOTOR-MOUNTS.md`. Smooth 9 mm idler spacers remain required.

Install 4 uxcell B0DP7173LB Ø5×10 mm and 6 MECCANIXITY B0FDQHC8SW Ø5×20 mm shoulder screws, both with 8 mm long M4×0.7 threads. Ø9 mm heads fit the planned pockets. M4 square nuts are 7×7×3 mm. A substitute with only 5 mm thread does not provide the planned engagement.

**Shorten only the four XY-joint threaded tips to 7.2–7.5 mm, measured from the end of the Ø5 shoulder.** Use soft vise jaws, file, deburr and test a nut by hand. Do not shorten or damage the smooth shoulder. The six fixed axles retain 8 mm threads.

| Position | Shoulder | Thread preparation |
|---|---:|---|
| Rear LU, native −X column | 20 mm | None |
| Rear LU, native +X column | 10 mm | None |
| Rear RU, both columns | 20 mm each | None |
| Front LD | 10 mm | None |
| Front RD | 20 mm | None |
| LJ1, left joint front pocket | 20 mm | 7.2–7.5 mm |
| LJ2, left joint angled pocket | 10 mm | 7.2–7.5 mm |
| RJ1, right joint front pocket | 10 mm | 7.2–7.5 mm |
| RJ2, right joint angled pocket | 20 mm | 7.2–7.5 mm |

Column names refer to native part coordinates, not an arbitrary machine view. `qa/shoulder-axles.json` records all ten cases and envelopes.

Set actual axial clearance to 0.1–0.3 mm using ID5/OD8 precision shims contacting inner bearing races only. Do not remove clearance by clamping the pulley. Preserve lower shims establishing belt planes. Nominal upper stacks: two fixed 10 mm axles get 0.5+0.3; two XY 10 mm axles get 0.3+0.3+0.2; six 20 mm axles get 0.5+0.5+0.5+0.3 mm. Including 12 original lower shims, totals are 32×0.5, 12×0.3 and 2×0.2 mm. Measure actual idlers and check free rotation; these are starting values. The 20×0.5 mm pack plus 48-piece assortment (12 each of 0.1/0.2/0.3/0.5 mm) covers the nominal stacks.

Each rear-idler brace needs one 1 mm M5 DIN125 washer under its extrusion-side M5×10: two washers total. Do not add washers to the brace’s other M5×12 screw.

## 412 head and tip

The modified cradle retains 4 M3×8 base and 2 FHCS M3×10 wall fasteners. Its 56 mm wall shifts the tip axis by 1 mm from the reference: recalibrate camera and coordinates.

Insert four M3 square nuts in rear cradle channels. Secure the 412 body with two bars and four M3×25. Bars bear on metal-frame edges: **do not clamp the coil, wire, spring or moving rod**. Slots allow ±3 mm vertical adjustment. Commercial mounting ears remain unused and clear; no M2 fasteners are required. Compare the received body against its drawing.

The coupler has two halves, two M3×16 screws and two M3 square nuts. It grips 6 mm of the 412’s Ø5×10 mm cap and retains the tip’s Ø8.9 mm collar. A 5.3 mm cavity allows nominal 0.4 mm clearance for the stated 4.9 mm stem. The threaded stem enters a smooth Ø6.2 cavity: **M5 pitch is not assumed and the thread is not the attachment**. Leave a small gap between halves; do not crush the cap or side-load the rod. Retain the collar while leaving the mesh free.

A third M3×6 screw with its own M3 square nut presses a flexible stripped lead against the metal tip stem; a Ø1.4 side channel guides it. Leave motion slack and strain-relieve the lead on the fixed structure. Check continuity to the mesh and isolate from coil wiring. This reference replaces the user’s hand capacitively, but effectiveness on the actual phone remains untested.

For an 8 mm thick bare phone, nominal geometry gives 4.4 mm retracted gap and 0.5 mm soft compression when extended. Initial body-height shift is 8 minus actual phone thickness in mm, limited to ±3. **This formula does not replace a contact test.** Start on a sacrificial surface, verify full return, measure force and use the minimum pressure that registers. Never drive a rigid stop into glass.

CAD uses the official drawing’s 4.9 mm stroke, not the rounded 5.5 mm listing description. Drive the 12 V / 0.3 A coil with the external MOSFET, never directly from a GPIO. Final wiring must be verified before energizing.

Initial development limits: maximum 1 second energized per action, rest at least 10 times the energized time and active fraction ≤10%. The datasheet’s 50% test at 1 s ON / 1 s OFF with 65 °C temperature rise **does not validate** a PETG cradle at that duty. Measure the cradle and motor supports; stop at 45 °C, deformation or failure to return. This external-temperature rule is provisional, not a certified operating limit or internal coil measurement. Firmware, watchdog and timeout are not implemented or validated in this release; implement and test them before AI actuation.

## Fasteners and nuts

| Fastener | Maximum installed quantity |
|---|---:|
| BHCS M3×6 | 9: 8 motors + 1 tip terminal |
| BHCS M3×8 | 42: 34 rail maximum + 4 belt clamp + 4 412 base |
| BHCS M3×10 | 4 |
| BHCS M3×16 | 2 coupler |
| BHCS M3×25 | 4 clamp bars |
| FHCS M3×8 | 4 bed |
| FHCS M3×10 | 10: 8 carriage + 2 412 wall |
| BHCS M5×10 | 6: 4 idler blocks + 2 brace to profile |
| BHCS M5×12 | 2 brace to block |
| BHCS M5×16 | 6: 4 feet + 2 motor A |
| BHCS M5×20 | 2 motor B |
| FHCS M5×12 | 6: 2 XY + 2 PCB + 2 tube |
| M5 DIN125 washer, 1 mm | 2 brace to profile |

The eight bracket kits add 16 M4 fasteners. Shoulder screws and shims are listed separately. M3 square nuts: 17 total, including seven new 412-head nuts. The 20 RN05BM5 allocate to 4 idler blocks + 4 motors + 2 X beam + 4 feet + 2 braces + 2 PCB + 2 tube bracket. Do not duplicate feet or retain eight M5 nuts from the superseded four corner plates.

Received rails may have fewer holes than the maximum 13+13+8 envelope. Use all available holes and retain surplus screws/nuts. Do not invent profile holes or force end alignment.

## Printed electronics

Print only `fdm_pcb_holder_electronics_x1`, replacing the simple PCB holder, plus `fdm_5648_retainer_x1`. The wing mounts Adafruit 5648 and the NKK S301 panel/guard. Four ties from the Fermerry kit pass through 6×3 mm slots; no new screws. Insulate both switch tabs individually. The open guard is low-voltage only, not a mains enclosure. See `ELECTRONICS.md`.

## Travel and commissioning

The 250 mm Y rail fits a 251 mm opening with nominal 0.5 mm end clearance. Initial X travel is limited by the 412 wall to 92 mm, centers −46..+46. Initial Y travel is 206 mm, carriage center CAD Z63.5..269.5. These are **geometry positions, not ready-to-use G-code coordinates or a homing origin**. Calibrate signs, origin, steps/mm and limits on the actual machine.

Digital checks cover 18 head poses (three X, three Y, two stroke states) against profiles, gusset envelopes, motor mounts and XY joints; six 412 height/stroke combinations; and ten idler axles. This is not a continuous sweep of belts, wiring, tools or all electronics. Manually check the full travel unpowered before installing a phone.

Acceptance sequence: coupons and small parts; squared frame; rail alignment; free idlers; motors/belts at low tension; free head return; wiring and cutoff; slow motion without phone; sacrificial-surface contact; thermal test; camera calibration; then brief phone taps. Confirm timeout and failure-release behavior before AI control. No physical acceptance test is completed in this release.

## Sources and reproduction scope

Editable STEP files and exported STL are available. The original private working environment used Python CAD-generation and integration scripts; those scripts, their dependencies and commercial references are not bundled here. Do not treat this archive as a self-contained regeneration pipeline. No firmware, credentials or G-code are included.

Sources: [PhysiClaw v0.51](https://github.com/physiclaw/PhysiClaw/releases/tag/physiclaw-hardware-v0.51), [FramingTech 10×20](https://www.framingtech.com/shop/10x20-05-mm-10mm-x-20mm-t-slot-profile-1-5mm-tslot-per-millimeter-402898), [GS20-05W](https://www.framingtech.com/shop/gs20-05w-gusset-20x20-with-5-slot-hardware-432568), [RN05BM3](https://www.framingtech.com/shop/rn05bm3-m3-roll-in-t-nut-with-ball-plunger-5-slot-484695), [RN05BM5](https://www.framingtech.com/shop/rn05bm5-m5-roll-in-t-nut-with-ball-plunger-5-slot-484697), [Adafruit 412](https://www.adafruit.com/product/412), [412 drawing](https://cdn-shop.adafruit.com/product-files/412/412_C514-B_diagram.PDF), [C514 datasheet](https://cdn-shop.adafruit.com/product-files/412/C514-datasheet.pdf), [mesh tip](https://www.amazon.com/dp/B0DSVSVSZN).

Retain LICENSE and PhysiClaw attribution when sharing derivatives. Manufacturing tolerances, incoming-part checks, thermal testing and touch quality remain real-build tasks.
