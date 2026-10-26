# Printed motor mounts A and B

Proposed PhysiClaw v0.51 variant, October 26, 2026. **Digitally checked; not printed or physically tested.** PETG is not assumed to have aluminum’s strength or thermal stability.

Print one of each final STL, millimeters, 100% scale. Outside plate faces are already on the bed at minimum Z=0. A and B have different legs and are not interchangeable.

| Part | Integrated legs | Print dimensions | Motor screws | Frame screws |
|---|---:|---|---|---|
| A | 8 mm | 60×42×14 mm | 4 BHCS M3×6 | 2 BHCS M5×16 |
| B | 12 mm | 60×42×18 mm | 4 BHCS M3×6 | 2 BHCS M5×20 |

Each replaces a 60×42×3 mm metal plate and two tube spacers. Four M5 frame T-nuts remain. Do not buy the superseded motor spacers; 9 mm idler spacers remain required.

## Interfaces

STEP uses native motor coordinates: face Z0, shaft X0/Y0, shaft pointing +Z. M3 pattern is 31×31 mm; M5 anchors X32/Y±12.5, profile-contact faces Z−8/−12. The plate thickens toward +Z to 6 mm; six head recesses keep seats at Z3. Motor face, screw lengths and nominal 5 mm M5 reach beyond the profile face remain. RN05BM5 entry is nominally 1.2 mm, leaving nominal 3.8 mm engagement. Verify received parts.

Center bore Ø25. Legs Ø16 with Ø5.7 M5 passages, joined by an 8×25 mm bridge within their envelope. Nominal motor-body clearance is 3 mm. M3 recesses Ø6.5, M5 recesses Ø10.5; do not add washers without recalculating reach. Heads must seat by hand rather than being forced into PETG. Minimum nominal outer M3 recess ligament is 1.25 mm in the outer plate half; the inner 3 mm retains passage geometry. Inspect the slicer and actual walls.

A includes Allen access channels in native −X/−Y directions, checked with a Ø3 tool envelope centered at Z6.75. B needs no channel, with tool center Z11.75. Original pulley hub bases remain A Z3 and B Z8; gaps 0/5 mm. Align the correct set screw with the shaft flat.

## Initial printing

Dry PETG, manufacturer profile, 0.4 mm nozzle, 0.2 mm layers, six walls, six top/bottom layers and 80% infill; legs/seats near-solid. Inspect layers. Bed-facing head pockets need clean bridges or removable local support, fully removed. No G-code or proven support-removal result is supplied.

## Digital checks and limits

`qa/motor-mounts.json` records valid single solids, closed oriented meshes, Z0 bed placement, STL volume error below 0.2% and zero-volume intersection with reference motor, pulley/set screws, six screws and two Ø3 Allen tools. Approximate solid volumes: A 14.31 cm³ and B 16.09 cm³. The slicer determines actual material/supports.

No full sweep against every frame component, belt path and wire is completed. Selective final integration is in `qa/integration.json`; it is not a continuous collision analysis.

## Prototype test

Assemble without phone, verify flat seating and free pulleys, begin with light tightening and moderate belt tension. Screws compress PETG over 11/15 mm and may lose preload through creep. No universal tightening torque is specified; do not solve deformation by tightening harder.

Measure motor face and support temperature during demanding sequences. Stop and investigate at **45 °C external support temperature**, deformation or shaft-position change. This unified development threshold is provisional, not certified service temperature. Recheck position and preload after cooling and after a prolonged test before using a phone.

Sources: original `hardware/parts/standard/bracket.py` and motor_10 through motor_30 procedures; [PhysiClaw](https://github.com/physiclaw/PhysiClaw/releases/tag/physiclaw-hardware-v0.51), [Prusa PETG guide](https://help.prusa3d.com/article/petg_2059). Regeneration scripts and commercial reference CAD are not part of this public archive.
