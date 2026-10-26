# living in a cat world · Project guide

Updated: October 26, 2026. DIY prototype without physical assembly or testing. Purchases resumed, one store at a time. See the current [purchase record](/purchases/) for confirmed orders and payment status.

## Goal

Build an AI that can perceive and act in the real world. The first project connects that goal to a concrete task: physically using an iPhone.

Use camera vision, XY motion and a vertically actuated capacitive stylus to operate an iPhone physically. First milestones: tap, double-tap, long press, swipe and drag with one contact point. One stylus cannot perform two-finger gestures. Extended autonomy and universal compatibility with every app are not demonstrated.

## Planned architecture

USB camera → Raspberry Pi 5 → observation/decision application → structured, validated actions → DLC32 V2.1 with two TMC2209 drivers → two NEMA 17 motors and CoreXY mechanics. Contact uses an Adafruit 412 12 V solenoid, 5648 MOSFET driver, printed coupler and 7 mm mesh tip. Final wiring and software need development and verification before connection to the phone.

The camera sits on an external arm. The Pi, 12 V machine and phone charger use separate supplies. The actuator branch includes a manual cutoff and 3 A fuse; cutting 12 V may leave logic powered over USB.

## Mechanics and printing

FramingTech slot-5 profiles: two 20×40 at 355 mm, two 20×40 at 190 mm, one 10×20 at 185 mm and two 10×20 at 190 mm. MGN9H rails: X 150 mm, two Y 250 mm. GT2 belt, 6 mm wide; drive pulleys for a 5 mm shaft. Consult the complete purchase record for exact fasteners and components.

The public archive includes 16 final STL and 16 STEP files, three fit coupons and CAD review records. The manifest specifies 22 installed printed parts. Print fit coupons in PETG first, then follow the final print manifest. Commercial reference CAD, full reference assemblies and self-contained regeneration scripts are excluded. Read the [release scope](../hardware/ft412/PUBLIC-RELEASE.md), [hardware guide](../hardware/ft412/README.md), [motor mounts](../hardware/ft412/MOTOR-MOUNTS.md) and [electronics mount](../hardware/ft412/ELECTRONICS.md) together.

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
