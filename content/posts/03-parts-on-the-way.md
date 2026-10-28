---
number: 3
slug: parts-on-the-way
date: "2026-10-27"
title: "The parts are on their way"
excerpt: "The printer is ordered, shipments are being tracked, and the first consolidation is full. Here is what has changed and what still needs to be tested."
---

**Update, October 27:** Three packages are now prealerted in a second consolidation, including a UPS shipment estimated to reach Miami on October 30. Speedy’s package listing now shows one earlier shipment received, although the consolidation view has not yet reflected it. The [shipment record](/shipments/) has the latest details.

The original report follows.

The project is moving from a design and shopping list toward a workbench full of real parts. The **Bambu Lab X2D AMS Combo is ordered**, the first shipments have tracking, and we have started consolidating packages for their trip to Costa Rica.

This is a progress report, not a claim that the robot works yet. The files are prepared, but we have not printed the components, assembled the machine, or tested a tap or swipe on the phone.

## The printer and the purchase record

The Bambu Lab order is **$881.86**, including the printer, an adapter, grouped other expenses, shipping and tax. The vendor's summary breaks it down as follows:

| Bambu order | USD |
|---|---:|
| Items before the order coupon | $847.18 |
| Printer coupon | −$30.00 |
| Shipping | $6.99 |
| Sales tax | $57.69 |
| **Order total** | **$881.86** |

The printer is $789.00 before the $30.00 printer coupon, and the adapter is $32.99. The remaining $25.19 in items is included as other expenses; the full $57.69 sales tax stays identified as tax. These figures are already part of the order total and must not be added again. The vendor displays a net payment of $881.86; we have not independently reconciled the bank transaction.

The original equipment planning estimate remains **$2,893.69**, including the owner's $500 unallocated allowance. It is a historical quote, not the amount spent: for example, it used the original $899 printer quote. Confirmed order totals and shipping charges belong in the purchase ledger instead.

As of this update, confirmed vendor order totals plus the first year of the domain add up to **$2,989.21**. This figure excludes MakerStore's **$10.18 provisional invoice request**, future forwarding costs, any further shipping adjustment and AI usage. It includes order totals that have not all been independently verified against bank charges; it is not a reconciled cash-spending total. FramingTech's shipping may change after weighing.

The [purchase record](/purchases/) keeps the quotes, vendor totals, actual tax, grouped other expenses and evidence level separate. We have not reconciled the contributions received, so there is no public balance yet.

## A first consolidation

Ten tracked packages have been prealerted and placed in the first project consolidation. That includes packages already in transit and packages whose labels have been created but which the carrier has not yet accepted. Once further packages are ready, we will use another consolidation when the forwarder allows it.

Amazon reports that one package was delivered to reception. At the time of the original report, the forwarder had not yet confirmed receipt, so we kept those two statuses separate. At the time, Bambu’s accessories were in a separate shipment and the printer was still preparing. Tracking numbers, addresses and original invoices remain in the private dispatch room.

Some prealert dates are **temporary estimates** entered to prepare the paperwork. They are not carrier promises or proof of delivery. The [shipment record](/shipments/) reflects what we can verify, without making those temporary dates into confirmed arrivals.

## What happens at the workbench

When the equipment arrives, the next steps are practical and measurable:

1. Check the contents and dimensions against the order and the design.
2. Print the three fit coupons in PETG and test them with the actual rails, fasteners and profiles.
3. Print the remaining brackets, joints and bed only after the critical fits have been checked.
4. Assemble the frame and motion system, then verify travel and limits before bringing the stylus to the phone.
5. Test capacitive contact, tapping and swiping, record the failures as well as the successes, and calibrate the camera to the machine.
6. Connect the observation and action loop once the individual movements are reliable enough to evaluate.

The design uses a single contact point, so simultaneous multi-touch gestures remain outside this version. Controller connections, touch force, stylus behavior and solenoid timing still require physical validation. A plausible CAD fit is a useful start; it is not a test result.

The [project documentation](/documentation/) and [CAD release](/documentation/hardware/) are already available to study and reuse. We will publish changes, measurements and results as the actual build takes shape.
