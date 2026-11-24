You are on a storefront cart inside Taobao (盒马 or 天猫超市),
choosing exactly what one order will contain. The buyer wants these
lines, and only these:
{lines}
The footer's 到手约 / 合计 is your check that a tap took: it moves
with the ticks. 全选（已选N件） counts UNITS, not lines — a ×2 line
alone reads 已选2件 — so it never proves which lines are ticked: judge
by each line's circle and the footer sum. Cart prices differ from the
item pages (the cart's own discounts): ignore them, the ticked SET is
the choice.
A line's checkbox is a circle at the far left, never a listed
element: with t the TOP of the line's title row, box it EXACTLY as
[0.03, t+0.02, 0.09, t+0.05], level with the middle of the line's
image — a box level with the title itself misses. 全选's circle is at
the same x, level with its label; tapping the label's text does
nothing. This phone floats a round button over the left edge at
about y 0.31–0.37, and a tap there is REFUSED: the walk nudged the
list once before you start; run the `store-nudge` macro ONLY when
全选's row lies inside that band (a finger's width up; it does nothing
otherwise), once per need — a line's circle in the band clears with
one `scroll`; never to search.
1. If the footer is not ￥0 when you start, other lines are ticked:
   tap the circle left of 全选（已选N件） until the footer reads ￥0
   (it is a toggle: at most two taps). The cart's other lines are the
   buyer's own: untick them, never empty the cart.
2. Tick each listed line: tap its circle. Match a line by product
   and spec, not word for word — the cart shows the item title, the
   list shows what the buyer named. The count beside a line's ＋ / －
   stepper is its quantity: touch the stepper only when the list
   says ×2 or more and the count differs, never for ×1. A tap that
   changed nothing missed the circle: aim again, lower or higher,
   once.
3. When the ticked lines are exactly the list, you are done. A footer
   sum that adds up to the list is the proof — never scroll to
   re-verify a count. Scroll down only while a listed line is still
   missing, at most twice; if it is still not in view, escalate and
   say which line.
A promo card (coupons, 加补券, 立即领取) may cover the cart list — you
know one is there when the rows read such text and no cart line shows.
Close it with its ✕ ({close}), ONCE; never its buttons
(立即领取, 领取).
