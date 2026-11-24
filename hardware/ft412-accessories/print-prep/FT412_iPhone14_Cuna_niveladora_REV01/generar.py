"""Entity / FT412 V1 — iPhone 14 leveling cradle, rev 01 (millimetres).

Phone screen faces up. Positive Y points to the notch and positive X to the
user's right. Z = 0 sits directly on the stock honeycomb bed. Run with
CadQuery 2.8: python generar.py [output directory].
"""
from pathlib import Path
import sys
import cadquery as cq

BODY_WIDTH, BODY_LENGTH = 71.52, 146.71
BED_CLEAR_WIDTH, BED_CLEAR_LENGTH = 84.0, 169.0
BED_CLEARANCE = 0.40   # each edge
PHONE_CLEARANCE = 0.30  # each fixed guide
SEAT_Z, GUIDE_RISE = 4.4, 3.0
TOP_Z = SEAT_Z + GUIDE_RISE
OUTER_W = BED_CLEAR_WIDTH - 2 * BED_CLEARANCE
OUTER_L = BED_CLEAR_LENGTH - 2 * BED_CLEARANCE
CAM_WINDOW = 39.0
NEAR_EDGE = 0.30
CAM_X = BODY_WIDTH / 2 - NEAR_EDGE - CAM_WINDOW / 2
CAM_Y = BODY_LENGTH / 2 - NEAR_EDGE - CAM_WINDOW / 2
NAME = "Entity_FT412_iPhone14_REV01"


def rounded_box(width, length, z0, z1, x=0.0, y=0.0, radius=1.0):
    return (cq.Workplane("XY", origin=(x, y, z0))
            .rect(width, length).extrude(z1 - z0)
            .edges("|Z").fillet(radius))


def guide(width, length, x, y):
    # The bevel contacts the side frame gently when the phone is lowered.
    return (rounded_box(width, length, SEAT_Z - 0.4, TOP_Z, x, y, 1.4)
            .edges(">Z").chamfer(0.65))


def build():
    floor = (rounded_box(OUTER_W, OUTER_L, 0, SEAT_Z, radius=3.0)
             .edges("<Z").chamfer(0.28))
    # Camera keepout on the right as seen through the screen, not the back.
    # Both lenses remain above the underlying FT412 bed even over a solid rib.
    openings = [
        (CAM_WINDOW, CAM_WINDOW, CAM_X, CAM_Y, 3.0),
        (38.0, 26.0, 0.0, -32.0, 7.0),
        (38.0, 26.0, 0.0, 4.0, 7.0),
        (22.0, 24.0, 0.0, -79.5, 3.2),     # Lightning cable, full-depth
        (25.0, 27.0, 43.0, -5.0, 6.0),      # finger access on open bed side
        (7.2, 33.0, 36.65, -44.0, 1.2),     # free travel for side spring
    ]
    for width, length, x, y, radius in openings:
        floor = floor.cut(rounded_box(width, length, -1, SEAT_Z + 1, x, y, radius))
    floor = floor.faces(">Z").edges().chamfer(0.30)

    x_stop = BODY_WIDTH / 2 + PHONE_CLEARANCE + 1.6
    y_stop = BODY_LENGTH / 2 + PHONE_CLEARANCE + 1.6
    rails = [guide(3.2, 16.0, -x_stop, -47.0),
             guide(3.2, 13.0, -x_stop, 55.5),
             guide(3.2, 13.0, x_stop, 55.5)]
    for x in (-18.5, 18.5):
        for y in (-y_stop, y_stop):
            rails.append(guide(13.0, 3.2, x, y))

    # A 1.6 mm in-plane leaf locates the phone against the left guides.
    # Its enlarged tip has 0.26 mm nominal interference when the phone is
    # seated against that datum. It prints on the bed along its whole length.
    leaf = rounded_box(1.6, 30.0, 0, TOP_Z, 37.45, -40.0, 0.72)
    tip = rounded_box(3.1, 7.2, 0, TOP_Z, 36.75, -53.7, 1.25)
    root = rounded_box(3.4, 7.0, 0, TOP_Z, 37.85, -26.0, 1.25)
    finger = leaf.union(tip).union(root).clean().faces(">Z").edges().chamfer(0.57)
    model = floor.union(finger)
    for rail in rails:
        model = model.union(rail)
    solid = model.clean().val()
    assert solid.isValid() and len(solid.Solids()) == 1
    return solid


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=True)
    result = build()
    cq.exporters.export(result, str(out / (NAME + ".step")))
    cq.exporters.export(result, str(out / (NAME + ".stl")), tolerance=0.025,
                        angularTolerance=0.09)
    print(f"Solid: {result.Volume():.1f} mm³")
