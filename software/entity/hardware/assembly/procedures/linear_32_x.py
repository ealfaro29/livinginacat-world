"""Linear X rail sub-assembly (short) — MGN9H 150 mm guideway with
M3 × 8 BHCS in the rail's mounting holes and hammer M3 T-nuts
hanging loosely from each shank tip, ready to engage.

Same construction as linear_10_y (LI10Y) — only the rail length and
slider position differ. The build logic is reused via inheritance;
this class just overrides three class attributes
(label, rail length, slider position).

Slider position:
  slider_position = 0.5 puts the slider centered along the rail
  (= world X = 0 after LI33X places the rail centered on world X = 0),
  matching the X-axis carriage's natural home position.

See linear_10_y for the full part list, geometry derivation, and
variant descriptions.

Run from the repo root:

    uv run --group cad python -m hardware step linear_32_x
"""

from hardware.assembly.procedures.linear_10_y import LI10Y
from hardware.assembly.travel_ranges import X_RAIL_LENGTH


class LI32X(LI10Y):
    compound_label = "linear_32_x"
    rail_length = X_RAIL_LENGTH  # mm — see assembly/travel_ranges.py
    slider_position = 0.5  # slider centered along the rail
