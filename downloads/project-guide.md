# Living in a Cat World · Project guide

FT412 is a CoreXY machine that operates an iPhone through its own touchscreen. V1 is the working, aluminum-frame prototype. V2 is a printed-enclosure design that reuses its main components. The physical tests below were performed on V1.

## Goal

A camera watches the phone. A carriage positions a mesh stylus over the glass, and a solenoid lowers it for a tap. The project tests what one physical point of contact can do, starting with taps and extending to holds and drags. Two-finger gestures require a second contact.

## Planned architecture

- **Vision and control.** A USB camera feeds a Raspberry Pi 5. The Pi sends motion commands over USB to a Makerbase MKS DLC32. The installed board is marked V2.2 and runs CoreXY firmware. A TS24-R touchscreen provides local controls.
- **Planar motion.** Two TMC2209 drivers operate two NEMA 17 motors. Two 6 mm GT2 belts move the bridge along the side rails and the stylus carriage across the bridge.
- **Touch.** An Adafruit 5648 MOSFET driver switches the Adafruit 412 solenoid. A two-piece printed coupler holds the capacitive mesh tip. On V1, a flexible 22 AWG lead from the side screw of the tip to the fixed aluminum frame provides the reference that worked in the phone test. [Stylus connection in the assembly guide](/documentation/assembly/#referencia-de-la-punta-en-el-marco)
- **Power.** V1 has separate supplies for the Pi, the 12 V mechanism and the phone. The actuator branch has a manual cutoff and a 3 A fuse. Logic can remain powered over USB after the 12 V supply is switched off.

The side control box was tried during assembly and removed when its components did not fit together. Its editor remains available as an earlier layout study. [Side-module editor](/tools/control-module/)

## Mechanics and printing

The V1 cut list specifies seven metric FramingTech slot-5 profiles. The two long sides are 20 × 40 × 355 mm. Two 20 × 40 × 190 mm profiles close the frame. The moving beam is 10 × 20 × 185 mm, and the two bed crossmembers are 10 × 20 × 190 mm. Two 250 mm Y rails carry the bridge. A 150 mm X rail carries the head. Each rail uses an MGN9H carriage.

The v0.1 release has 16 printable designs and their editable STEP files, plus three fit coupons. Its manifest calls for 22 installed printed pieces. The owner reported completing those prints. The illustrated guide identifies each part, the matching fasteners and the nuts that must go into a slot before the frame is closed. [Assembly guide in Spanish](ASSEMBLY-ES.md) · [Hardware guide](../hardware/ft412/README.md) · [Release scope](../hardware/ft412/PUBLIC-RELEASE.md)

Two separate REV01 downloads address fit problems found during assembly. The revised cradle moves two ribs away from the belt clamp. The revised coupler fits the owner's measured 8.83 mm collar and 7.90 mm mesh tip. The owner installed the revised coupler and checked that the tip was retained and returned freely with power off. The installed cradle revision was not recorded. [Cradle correction](/documentation/cradle-rev01/) · [Tip coupler correction](/documentation/coupler-rev01/) · [Motor mounts](../hardware/ft412/MOTOR-MOUNTS.md) · [Electronics mount](../hardware/ft412/ELECTRONICS.md)

## What V1 demonstrated

| Bench check | Observation |
|---|---|
| Mechanical assembly | The owner fitted the frame, feet, phone bed, rails, motors, idlers and both belts. They reported smooth manual travel with the right rail tightened. |
| X travel | With a physical ruler zeroed at the carriage, a command for 10 mm to the right produced a reported 10 mm movement. |
| Y travel | With the ruler aligned front to back, a command for 10 mm toward the rear also produced a reported 10 mm movement. |
| Contact | The owner reported that the iPhone Calculator registered a stylus tap with the tip connected to the machine's aluminum frame. |

The ruler checks cover one move on each axis at the ruler's resolution. A screen-wide error map, repeatability after reseating the phone, and sustained thermal performance still need measurement. [Fit checks](/documentation/fit-checks/)

## V2 design dimensions

V2 integrates the phone bed, electronics compartment and camera support into a printed console. Its drawing places the lens 100 mm above the glass, based on the owner's measurement of V1. At that setting the modeled exterior is **196 × 302 × 231 mm**. The calculated travel with the three carriages fully supported and 2 mm reserved at each rail end is **106.1 mm in X and 206.1 mm in Y**. These are V2 CAD results. Physical fit, belt clearance under tension and thermal behavior need a built prototype. [Explore V2](/v2/)

## Build and verification order

1. Check the component markings, cut lengths and fastener sizes against the illustrated guide.
2. Print the fit coupons before committing to a full batch. Check the actual screws, nuts and tip.
3. Square the frame and align the rails with the phone removed. Check free movement, belt tension and cable clearance along the full travel.
4. Disconnect power before fitting motors or drivers. Verify pin assignments, wiring and polarity against the actual boards.
5. Start with slow, short moves and a physical reference. Check axis direction, travel limits and the cutoff before approaching the phone.
6. Test tip retention, retraction and contact on a sacrificial surface at screen height.
7. Align the camera with all four screen corners visible, calibrate camera coordinates to the machine and measure error across the screen.
8. Run supervised gesture tests before enabling automated tasks.

## Provisional contact limits

The solenoid is designed for intermittent use. For development, limit each energization to **1 second** and allow at least **10 times its duration** before the next pulse. Stop if the measured external temperature at the coil body or mount reaches **45 °C**, the printed support deforms, or the tip fails to retract. An external reading measures the surface. Internal coil temperature and the duty cycle of a finished device still need separate validation.

Test the timeout and retraction behavior before automated operation. A tap that works once does not establish a safe hold or drag duration.

## Planned acceptance tests

- Measure tap accuracy with a grid covering the center, edges and corners. Record attempts, detections and position error.
- Record timing and travel for double taps, long presses, swipes and drags.
- Repeat the grid after removing the phone, replacing it in the bed and recalibrating.
- Test behavior with reflections, an obscured camera, a changed screen or a missed touch.
- Check the manual cutoff, timeout and retraction. Identify every circuit that stays live through USB.
- Measure temperature and wear under representative sequences before extended operation.

## Data and transparency

The V1 catalog lists the equipment used for the project and its approximate overall investment. The V2 section presents the digital assembly, fastening details and design checks. [V1 components](/v1/) · [V2 model](/v2/) · [Attribution and licenses](ATTRIBUTION.md)
