# Public release scope

16 final STL designs and their 16 STEP files; 22 installed printed parts plus three fit coupons. The v0.1 archive remains the original digital-review snapshot, with its checksum unchanged. Use `qa/print-manifest.json` for quantities and `README.md` for planned assembly.

**Coupler fit correction, November 17, 2026:** the separate [coupler REV01 pair](/documentation/coupler-rev01/) incorporates the owner's tip measurements and replaces the two original halves. The owner subsequently confirms both replacement halves printed and installed, and reports completing the unpowered retention/return check before requesting continuation. Actual event dates, measured printed roundness and powered or thermal performance were not supplied. Solenoid-cap and fastener features are preserved. This does not alter the original archive or add installed parts.

**Cradle fit correction, November 17, 2026:** the original L-shaped cradle has rib interference with the belt clamp. Use the separate [cradle REV01 replacement](/documentation/cradle-rev01/) for its next physical fit trial. The six mounting holes and four captive-nut cavities are unchanged. Digital collision checks pass; the corrected part has not yet been printed or physically tested. This replaces one cradle and does not add an installed piece or modify the original v0.1 archive.

Current build observations, reported November 13, 2026: the first test batch is complete and the owner reports M3 and M5 checks passed in PLA Silk with a 0.4 mm nozzle. M4, coupler fit, PETG and full assembly acceptance remain unvalidated. Results for each hole, pocket and head seat were not individually itemized. These observations do not certify the archive or change its geometry. See the [dated fit-check report](/documentation/fit-checks/).

This release excludes commercial `vendor/`, `reference_step/`, `original_stl/`, `upstream/`, reference assemblies and regeneration scripts that depend on them. Intermediate CAD records may describe the larger private working environment; they are not additional printable parts or a self-contained regeneration pipeline.

Public instructions are in English. Machine-generated CAD review artifacts retain their original identifiers and some original-language annotations. They are evidence snapshots, not proof of physical performance.

The provisional development temperature stop is unified to 45 °C on externally measured body/support surfaces, alongside the guide’s timing limits. This unvalidated rule does not measure internal coil temperature.
