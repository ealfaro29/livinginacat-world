"""Motor bridge reinforcement and a removable carrier for an already printed R01 shell.

Dimensions are in the console STEP coordinate system; Y increases toward the rear.
"""

from build123d import Plane, Polygon, Pos, SlotCenterToCenter, extrude, loft
from geometria import block, bore

MOTORS = ((-31.0, 84.3, -1), (21.0, 91.3, 1))
IDLER_Y = 279.5
FRONT, BACK = 253.8, 296.5


def wall(x0, x1, outline):
    face = Plane.YZ.offset(x0) * Polygon(*outline, align=None)
    return extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def side_block(x, side, near, far, y0, y1, z0, z1):
    a, b = sorted((x + side * near, x + side * far))
    return block(a, b, y0, y1, z0, z1)


def side_web(x0, x1, bottom, ceiling):
    # The two heels stand forward of the power inlet. The diagonal carries
    # the aft end of the rail and clears the DC socket and its screw heads.
    return wall(
        x0,
        x1,
        [
            (253.8, bottom),
            (273, bottom),
            (273, 44),
            (296.5, 69),
            (296.5, ceiling),
            (253.8, ceiling),
        ],
    ).cut(
        wall(
            x0 - 0.2,
            x1 + 0.2,
            [(257.8, 10), (268.8, 10), (268.8, 49), (286.5, 68), (257.8, 68)],
        )
    )


def old_post_space():
    return [block(-9.85, -0.15, y - 3.4, y + 3.4, 2.0, 91.75) for y in (260, 290)]


def flush_slots(plate):
    # Ø7 x 90 degree countersinks swept 4 mm along Y. A #7213 M3x8
    # flat-head screw has an 8 mm overall length, including its head.
    for x in (21 - 15.5, 21 + 15.5):
        y = 259.5
        cutter = loft(
            [
                Pos(x, y, h) * SlotCenterToCenter(4, d, rotation=90)
                for h, d in ((94.50, 3.45), (96.45, 7.35))
            ]
        )
        plate = plate.cut(cutter)
    return plate.clean()


def reinforce(case):
    additions = []
    for x, z, outer in MOTORS:
        post = -62.25 if outer == -1 else 52.25
        # With the motor adjusted +/- 2 mm, its sides end at +/- 21.15.
        for side in (-1, 1):
            a, b = sorted((x + side * 21.7, x + side * (28 if side == outer else 25.4)))
            web = side_web(a, b, 2.4, z + 3.4)
            cheek = side_block(
                x, side, 18.9, 28 if side == outer else 25.4, FRONT, BACK, z, z + 5
            )
            # Preserve the idler shoulder and the side-entry M5 nut pocket.
            keepout = bore(post, IDLER_Y, 2.0, 14.6, 100)
            access = block(post - 4.45, post + 4.45, 274.4, 300, 93.2, 98.2)
            additions.extend([web.cut(keepout, access), cheek.cut(keepout, access)])
    return flush_slots(case.fuse(*additions).clean())


def carrier():
    # Both original plates enter from the rear on a bench. The rims overlap
    # the top of each plate, clear all four screw heads and keep the motor at
    # exactly its former height. An M3 cross-bolt closes each rear entrance.
    parts = [block(-56, 46, 248.0, 251.1, 68, 76)]
    for x, z, outer in MOTORS:
        for side in (-1, 1):
            outside = side == outer
            span = 28.0 if outside else 25.45
            a, b = sorted((x + side * 21.75, x + side * span))
            # The front edge of each upright shares the printing plane with the bridge.
            web = side_web(a, b, 3.0, z)
            leg = side_block(x, side, 22.0, span, 248.0, 258, 68, 78)
            bottom = side_block(x, side, 21.75, span, 252.5, 297.8, z - 3.6, z)
            rail = side_block(x, side, 23.35, span, 250, 298.8, z - 2, z + 7.9)
            rim = side_block(x, side, 19.35, span, 253.4, 298.8, z + 5.32, z + 7.9)
            stop = side_block(
                x, side, 19.35, span, 252.0, FRONT - 0.30, z + 2.72, z + 7.9
            )
            parts.extend([web, leg, bottom, rail, rim, stop])
            if outside:
                parts.append(
                    side_block(x, side, 22.0, 29.25, 294.2, 301.95, z - 2.6, z + 7.9)
                )
        # Two storeys around the rear idler: the flared shoulder locates XY;
        # the open window under it takes a tie around the narrow neck + lug.
        pin = -62.25 if outer == -1 else 52.25
        ring_parts = []
        for zz in (82.5, 90.5):
            ring_parts.append(bore(pin, IDLER_Y, zz, 23.0, 2.4))
            ring_parts.append(
                side_block(x, outer, 23.5, 31.5, IDLER_Y - 4, IDLER_Y + 4, zz, zz + 2.4)
            )
        ring_parts.append(
            side_block(pin, outer, 8.2, 11.5, IDLER_Y - 2.3, IDLER_Y + 2.3, 84.7, 90.8)
        )
        parts.extend(ring_parts)
    shape = parts[0].fuse(*parts[1:])
    # Vertical assembly over a complete 13.6 mm idler shoulder is possible
    # even when the lower collar rests next to its narrower 9 mm shank.
    shape = shape.cut(*(bore(x, IDLER_Y, 2.8, 14.6, 105) for x in (-62.25, 52.25)))
    # Clear the square motor housings even at both ends of belt adjustment;
    # the outer annuli are wider than the plate rails at this station.
    for x, z, outer in MOTORS:
        shape = shape.cut(block(x - 21.65, x + 21.65, 251.4, 298.65, 3.0, z))
        # Cut outside the plate slide envelope only once after the webs,
        # tie ears and collars have all been joined.
        shape = shape.cut(block(x - 23.34, x + 23.34, FRONT - 0.29, 302.2, z, z + 5.32))
        # A standard #7219 M3 x 8 enters from the outer face. Its end
        # projects across the entrance, just behind the plate.
        tip = x + outer * 29.35
        hole = bore(tip, 298.25, z + 2.0, 3.4, 9.4, (-outer, 0, 0))
        nut = side_block(x, outer, 24.35, 27.10, 295.34, 301.16, z - 0.86, z + 8.2)
        pin = -62.25 if outer == -1 else 52.25
        access = block(pin - 4.45, pin + 4.45, 274.4, 300, 93.2, 98.2)
        shape = shape.cut(hole, nut, access)
    # The moving belt clamp reaches the front of the higher pocket at the
    # back of its travel. Keep its full swept envelope free. The longer
    # rear sections still capture each plate from above.
    head_clearance = block(-76, 66, 245, 266.0, 96.25, 105)
    shelf_clearance = block(-76, 66, 245, 253.45, 79.45, 86.65)
    coil_clearance = block(-76, 66, 245, 252.0, 79.45, 105)
    return shape.cut(
        *old_post_space(), head_clearance, shelf_clearance, coil_clearance
    ).clean()
