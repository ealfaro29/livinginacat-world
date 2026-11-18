# living in a cat world · Project guide

**Side control module, November 17.** The owner's layout uses a 280 × 120 × 90 mm enclosure outside the left rail when viewed from the front. A 30 mm lip leads to a 45° panel for the TS24-R display. The incline runs 60 mm horizontally, including the first 55 mm reserved for the display. The Raspberry Pi 5 sits ahead of the DLC32, with the MOSFET and fuse holder alongside. The rear panel holds the power cable pass-through and cutoff switch, the fan opens to the top, and the rail-facing wall has honeycomb ventilation. Internal clips guide the wiring. Floor mounts carry the boards and fuse holder. The layout and print split are editable in the [control module designer](/tools/control-module/). Final CAD awaits measurements of the parts, cutouts, cables and fasteners.

**Current assembly, November 17:** the owner confirms the electronics support mounted and reports an uneven underside. A separate optional 75 × 75 mm cosmetic plate and raised symbol are prepared as two separate parts, without clips or holes. The logo uses nominal Color Mix 90% yellow and 10% black and its matching job was observed starting at 0/12 layers, without completion confirmed. The black plate remains separate without a confirmed print; preserve the honeycomb openings when fitting the plate. The original 22-part manifest and archived CAD remain unchanged.

Start assembling with the [illustrated Spanish assembly guide](ASSEMBLY-ES.md), including a printable PDF, exact fasteners, frame orientation and checks for each stage.

**Later November 17 update:** the owner reports the solenoid installed with two bars and four screws. The original tip-coupler pair was reported awkward and apparently oval; the tip was measured and [coupler REV01](/documentation/coupler-rev01/) was prepared, saved and natively sliced. At the owner's explicit instruction the two replacement halves were sent to print in PLA with 0.16 mm layers and the main 0.4 mm nozzle. The matching job was observed active at 0/48 layers in initial preparation. The owner subsequently confirms both replacement halves printed and installed, and reports completing the unpowered retention/return check before requesting continuation. Actual event dates, measured printed roundness and powered or thermal performance were not supplied. The original 22-part print completion and historical CAD archive remain preserved.

**Assembly update, November 17:** the owner reports the frame, bed, rails, motors, idlers and both belts assembled, with smooth manual travel. The original L-shaped cradle cannot seat because its two ribs interfere with the belt clamp. [Cradle REV01](/documentation/cradle-rev01/) corrects that interference in CAD, preserving mounting holes and nut cavities. At that earlier review, the replacement cradle had not been sliced or sent. The owner later reports the solenoid installed without identifying the printed cradle revision; no additional cradle print is scheduled by this completion update. The original 22-piece completion record and v0.1 archive remain intact. Powered operation and complete assembly acceptance remain unconfirmed.

Updated: November 16, 2026 (Costa Rica). The owner confirms all project prints are complete and requests assembly. The electronics support retains its earlier observed yellow PLA and Generic PLA High Speed material evidence; no new printer observation was made. The original PETG preparation stays unchanged. Saved native history reports the solenoid cradle and two bars as Success. The first coupons/coupler, bed/four feet and motor-mount/belt-clamp batches retain their completion evidence. The owner now confirms eight finished pieces by count and shape groups, matching the preceding PETG plate. All 22 installed pieces have prepared files and recorded print completion. The exact completion event date, quality and measured fit were not supplied. No additional plate is scheduled. We can begin dry frame and rail assembly now. Fit of the complete assembly, the switch and coupler, motion, touch and heat/load behavior remain unvalidated.

On November 15 the owner confirmed physical receipt of the existing project shipments matched to the received consolidations, and separately confirmed the controller. Actual delivery dates were not specified. Purchase quantities, original documents, forwarding assignments and earlier carrier evidence are preserved. The combined forwarding amount remains pending reconciliation without a numeric total; recipient receipt does not itself establish payment or a container billing relationship.

Mouser shipped all ten replacement references. Its final invoice totals $87.22, superseding the $82.07 order confirmation, and explicitly reports paid in full; bank settlement remains unverified. FedEx confirms carrier delivery on November 9, and Speedy receipt in Miami was verified on November 10 through an independently verified full carrier alias. On November 14 Speedy confirmed the exact shipment in Costa Rica. On November 15 the owner confirms physical receipt; the actual arrival and recipient-delivery event dates remain unspecified. The original invoice, prealert and consolidation are complete. The Adafruit 412 solenoid, 5648 driver and original harness references are retained. NKK S301T replaces S301 and uses screw terminals; check the printed guard and terminal clearance before assembly. The planned local purchase of suitable 18 AWG stranded copper wire remains unconfirmed. Its supplier, length and price are unknown; there is no confirmed Remington order.

The [Amazon DLC32 V2.1 replacement kit](https://www.amazon.com/dp/B0GY43P1CL) was ordered on November 7. Amazon confirms carrier delivery on November 10 for the controller's exact fulfillment group, and Speedy receipt in Miami was verified on November 11. On November 14 Speedy confirmed the exact controller shipment in Costa Rica. On November 15 the owner separately confirms receiving that exact controller shipment; the actual arrival and recipient-delivery event dates remain unspecified. Its authentic purchase receipt, unique prealert and consolidation are complete; a merchant payment observation does not establish bank settlement or a final tax invoice. Consult the shipment record for its current forwarding location. VXB confirmed cancellation and reports a full refund; bank receipt remains unverified. Its original amounts and shipment remain cancelled history. The [reference configuration](https://github.com/physiclaw/PhysiClaw/blob/main/firmware/config.yaml) specifies MKS DLC32 V2.1 and CoreXY. The published V2.1 schematics, pinout and dimensions match the Makerbase documents; physical inspection and commissioning remain necessary. Keep the two TMC2209 drivers already ordered.

## Goal

Build an AI that can perceive and act in the real world. The first project connects that goal to a concrete task: physically using an iPhone.

Use camera vision, XY motion and a vertically actuated capacitive stylus to operate an iPhone physically. First milestones: tap, double-tap, long press, swipe and drag with one contact point. One stylus cannot perform two-finger gestures. Extended autonomy and universal compatibility with every app are not demonstrated.

## Planned architecture

USB camera → Raspberry Pi 5 → observation/decision application → structured, validated actions → DLC32 V2.1 with two TMC2209 drivers → two NEMA 17 motors and CoreXY mechanics. Contact uses an Adafruit 412 12 V solenoid, 5648 MOSFET driver, printed coupler and 7 mm mesh tip. Final wiring and software need development and verification before connection to the phone.

The camera sits on an external arm. The Pi, 12 V machine and phone charger use separate supplies. The actuator branch includes a manual cutoff and 3 A fuse; cutting 12 V may leave logic powered over USB.

## Mechanics and printing

Planned FramingTech slot-5 profile cuts: two 20×40 at 355 mm, two 20×40 at 190 mm, one 10×20 at 185 mm and two 10×20 at 190 mm. The owner counted seven received profiles with the expected relative size groups; exact cut lengths were not measured and the count does not confirm every fastener. MGN9H rails: X 150 mm, two Y 250 mm. GT2 belt, 6 mm wide; drive pulleys for a 5 mm shaft. Consult the complete purchase record for exact fasteners and components.

The public archive includes 16 final STL and 16 STEP files, three fit coupons and CAD review records. The manifest specifies 22 installed printed parts. Initial M3 and M5 checks were reported passed in PLA Silk with a 0.4 mm nozzle; M4 screw/nut fit was also reported passed on November 15; coupler fit remains pending. Hole, pocket and seat results were not individually itemized. Follow the original quantities and verify the remaining interfaces, motor heating and loaded behavior in the current build before accepting the assembly; the prior Silk fit results do not validate PETG. The archive's PETG preparation remains a historical design reference, with its original checksum and geometry unchanged. Commercial reference CAD, full reference assemblies and self-contained regeneration scripts are excluded. Read the [release scope](../hardware/ft412/PUBLIC-RELEASE.md), [hardware guide](../hardware/ft412/README.md), [motor mounts](../hardware/ft412/MOTOR-MOUNTS.md) and [electronics mount](../hardware/ft412/ELECTRONICS.md) together.

The electronics support is complete by the owner report of November 16. Its prior device estimate of 3 h 47 min 26 s and 60.00 g remains historical, not measured duration or consumption. Check the existing printed pieces against the 22-piece manifest before assembling the transmission. Start with frame squareness, feet and rail alignment. The local wire purchase and receipt of the specified grease remain pending for later wiring and commissioning.

## Build and verification order

1. Receive and measure components; record any model or quantity differences.
2. Print fit coupons and check sockets before the final batch.
3. Assemble the frame, rails and transmission without the phone. Check squareness, belt tension, free movement and clearances.
4. Verify wiring and polarity against each component’s documentation. Do not connect motors or drivers while powered. Verify pin assignments before energizing.
5. Test slow motion, axis direction, software limits and actuator cutoff. Do not assume automatic homing or collision detection.
6. Separately test tip retraction, force, return and capacitive recognition. Establish pulse/rest parameters using measurements.
7. Calibrate the camera-to-XY transformation and measure error across the screen.
8. Test supervised gestures and record results before adding AI control.

## Provisional contact limits

The solenoid is intermittent-duty. Initial development limits: no more than 1 second energized per action; rest at least 10 times the energized duration; stop if externally measured body/mount temperature reaches 45 °C. These are unvalidated development rules, not demonstrated operating specifications, and do not measure the internal coil temperature. Swipe, drag and hold capability must be demonstrated within the permitted thermal cycle. Implement and test timeout and safe retraction before AI operation.

## Planned acceptance tests

- A tap grid including edges and corners: publish coordinates, attempts, successes and observed error.
- Double-tap, long press, swipes in four directions and drag: record duration, travel and result.
- Repeatability after replacing the phone and recalibrating.
- Camera occlusion, reflections, screen changes and failed actions: stop or recover explicitly, without unlimited retries.
- Manual cutoff and timeout: verify actuator behavior and identify circuits that remain powered.
- Thermal and wear testing under realistic sequences. Do not claim extended unattended operation before validating it.

## Data and transparency

Current parts and purchase status: https://livinginacat.world/purchases/. Shipments: https://livinginacat.world/shipments/. USD; quotes exclude tax and shipping unless noted. Ordered, paid, shipped and delivered are distinct states. API usage, substitutions and unknown charges will be added as verified.

Mechanical foundation: PhysiClaw hardware v0.51 under MIT; [attribution](ATTRIBUTION.md). This variant and its limits are documented independently. Source: https://github.com/ealfaro29/livinginacat-world.

The owner confirmed a $537.00 TechStorex project expense, recorded once under Taxes, tariffs, shipping and others. It is a standalone additional expense with no shipping or equipment allocation; it does not create a parcel to prealert. Payment evidence is retained privately and bank settlement remains unverified.
