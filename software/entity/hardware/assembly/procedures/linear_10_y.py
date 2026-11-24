"""Linear Y rail sub-assembly — one MGN9H 240 mm guideway with an
M3 × 8 BHCS in every mounting hole (see ``mgn9h.rail_hole_xs`` for
why every hole) and an M3 hammer T-nut ready to engage each.

Geometry in the rail's native frame (matches MGN9H — rail bottom
face at native Z = 0, length axis along native X):
  * Each BHCS seats on the floor of the rail's flat-bottom
    counterbore (mgn9h.rail_cbore_floor_z — see the hole constants
    there for why a cylindrical head, and why M3 × 8). Its head stays
    below the rail top; the shank protrudes BHCS_LENGTH minus the rail
    under the seat into the slot, where the hammer T-nut catches it,
    and must end above extrusion_spec.slot_depth.
  * Each hammer T-nut HANGS LOOSELY from its screw's shank tip —
    only TNUT_LOOSE_ENGAGEMENT mm of the shank is inside the bore.
    This is the pre-install state: the bundle (rail + screws +
    t-nuts) is ready to be pressed onto an extrusion slot. Final
    tightening on the slot pulls each t-nut up the shank until the
    plate top catches the slot lip (1.8 mm inside the slot face,
    derived from leg - slot_lip_under_y) — not modeled here.
  * The t-nut's placement plane maps its native +Y (plate depth /
    bore axis) → rail +Z so the bore aligns with the screw shank,
    and native +Z (slot length) → rail +X.

Two variants:
  * exploded — screws lifted SCREW_EXPLODE above the rail top face;
               t-nuts dropped TNUT_EXPLODE below their loose-hang
               position. Reads as "fasteners ready to assemble onto
               the rail."
  * assembled — screws seated in the rail with t-nuts hanging
                loosely from each shank tip.

Run from the repo root:

    uv run --group cad python -m hardware step linear_10_y
"""

from build123d import Compound, Location, Plane

from hardware.assembly.base import ASSEMBLED_CAM0, EXPLODED_CAM0, BaseAssembly
from hardware.assembly.projection import FRONT_LEFT_HIGH
from hardware.assembly.travel_ranges import Y_RAIL_LENGTH
from hardware.parts.standard.mgn9h import (
    MGN9H,
    rail_cbore_floor_z,
    rail_hole_xs,
)
from hardware.parts.standard.mgn9h import (
    slider_position as default_slider_position,
)
from hardware.parts.standard.screw import Screw
from hardware.parts.standard.t_nut import (
    HAMMER_TOTAL_HEIGHT,
    TNut,
)
from hardware.parts.standard.t_nut import (
    LENGTHS as TNUT_LENGTHS,
)

RAIL_LENGTH = Y_RAIL_LENGTH  # mm — MGN9H rail length — see assembly/travel_ranges.py
BHCS_LENGTH = 8  # mm — M3 BHCS underhead length
TNUT_LOOSE_ENGAGEMENT = 1  # mm — assembled: shank depth inside the bore at
#      loose hang (a few threads — the bundle is
#      ready to drop onto an extrusion slot)
SCREW_EXPLODE = 20  # mm — exploded: screws lifted above rail top
TNUT_EXPLODE = 15  # mm — exploded: t-nuts dropped below loose hang


class LI10Y(BaseAssembly):
    # Subclasses share this build logic and only override the three
    # class attributes below — ``compound_label`` retargets the
    # STEP / SVG filename, ``rail_length`` swaps in a different MGN9H
    # length (the screws follow its holes), and ``slider_position``
    # (0.0 = -X end, 1.0 = +X end) moves the slider along the rail.
    # ``_module_stem()`` already derives the output filename from the
    # subclass's own module, so no other override is needed.
    compound_label: str = "linear_10_y"
    rail_length: float = RAIL_LENGTH
    slider_position: float = default_slider_position
    camera = FRONT_LEFT_HIGH
    views = [EXPLODED_CAM0, ASSEMBLED_CAM0]

    def _build(self) -> Compound:
        mgn = MGN9H(
            rail_length=self.rail_length,
            slider_position=self.slider_position,
        ).build()

        screw_xs = rail_hole_xs(self.rail_length)  # a screw in every hole

        tnut_length = TNUT_LENGTHS["hammer"]

        # T-nut hangs loosely from the shank tip with only
        # TNUT_LOOSE_ENGAGEMENT mm of shank inside the bore. The
        # bore's far end (boss top, at t-nut native Y =
        # HAMMER_TOTAL_HEIGHT) maps to rail Z = origin.z +
        # HAMMER_TOTAL_HEIGHT via the placement plane (native +Y →
        # rail +Z); solving for origin.z gives the loose-hang z.
        screw_z_seated = rail_cbore_floor_z  # underhead on the cbore floor
        shank_tip_z = screw_z_seated - BHCS_LENGTH
        tnut_z_loose = shank_tip_z + TNUT_LOOSE_ENGAGEMENT - HAMMER_TOTAL_HEIGHT
        if self.exploded:
            screw_z = screw_z_seated + SCREW_EXPLODE
            tnut_z = tnut_z_loose - TNUT_EXPLODE
        else:
            screw_z = screw_z_seated
            tnut_z = tnut_z_loose

        attachments = []
        for sx in screw_xs:
            screw = Screw("BHCS", "M3", BHCS_LENGTH).build()
            screw.move(Location((sx, 0, screw_z)))
            attachments.append(screw)

            nut = TNut("hammer", "M3").build()
            nut.move(
                Location(
                    Plane(
                        origin=(sx - tnut_length / 2, 0, tnut_z),
                        x_dir=(0, 1, 0),
                        z_dir=(1, 0, 0),
                    )
                )
            )
            attachments.append(nut)

        return Compound(label=self.compound_label, children=[mgn, *attachments])
