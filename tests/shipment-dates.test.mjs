import test from "node:test";
import assert from "node:assert/strict";
import { dateTime, shipmentCarrierDate } from "../scripts/lib.mjs";

test("carrier delivery takes precedence over an earlier delivery estimate", () => {
  assert.deepEqual(shipmentCarrierDate({ status: "carrier_delivered", carrierDeliveredDate: "2026-11-13", expectedDeliveryDate: "2026-11-17" }),
    { label: "Carrier delivery", value: "2026-11-13", confirmed: true });
});
test("an undated confirmed delivery does not reuse its estimated date", () => {
  assert.deepEqual(shipmentCarrierDate({ status: "carrier_delivered", expectedDeliveryDate: "2026-11-17" }),
    { label: "Carrier delivery", value: null, confirmed: true });
});
test("a shipment in transit keeps its date explicitly estimated", () => {
  assert.deepEqual(shipmentCarrierDate({ status: "shipped", expectedDeliveryDate: "2026-11-17" }),
    { label: "Estimated carrier arrival", value: "2026-11-17", confirmed: false });
});
test("a confirmed return does not present an old estimate as an arrival", () => {
  assert.deepEqual(shipmentCarrierDate({ status: "returned", expectedDeliveryDate: "2026-11-17" }),
    { label: "Carrier return", value: null, confirmed: true });
});
test("planned dispatch remains distinct from estimated arrival", () => {
  assert.deepEqual(shipmentCarrierDate({ status: "preparing", expectedShipDate: "2026-11-17" }),
    { label: "Planned dispatch", value: "2026-11-17", confirmed: false });
});
test("review timestamps use the owner's date across UTC midnight", () => {
  const text = dateTime("2026-11-14T05:05:00Z");
  assert.match(text, /November 13, 2026/);
  assert.match(text, /11:05/);
  assert.match(text, /Costa Rica/);
  assert.equal(dateTime(null), "Unconfirmed");
});
