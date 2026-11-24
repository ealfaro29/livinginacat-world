import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("./site/ui/portal.js", import.meta.url), "utf8");
async function openDashboard(hardware, failArm = false) {
  const nodes = new Map();
  const writes = [];
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, {
      hidden: true, dataset: {}, handlers: {}, classList: {toggle() {}},
      addEventListener(event, handle) { this.handlers[event] = handle; },
    });
    return nodes.get(id);
  }
  const document = { documentElement: {lang:"es"}, hidden:false, getElementById:node,
    querySelectorAll:() => [], addEventListener() {} };
  async function fetch(path, options = {}) {
    if (options.method !== "POST") return Response.json({hardware: {...hardware}});
    writes.push(path);
    if (path === "/api/connect-arm" && failArm) return Response.json({status:"error",error:failArm}, {status:409});
    if (path === "/api/connect-arm") hardware.arm = true;
    if (path === "/operator/connect-camera") hardware.camera = true;
    return Response.json({status:"ok"});
  }
  let poll;
  vm.runInNewContext(source, { document, window:{addEventListener(){}}, fetch, setInterval(fn){poll = fn;} });
  await new Promise(resolve => setImmediate(resolve));
  return {node, writes, poll};
}
test("opening the dashboard is read-only; a user click connects the two devices once", async () => {
  const {node,writes} = await openDashboard({arm:false,camera:false,bridge:true});
  const button = node("connect-all");
  assert.equal(button.disabled, false);
  assert.deepEqual(writes, []);
  await Promise.all([button.handlers.click(), button.handlers.click()]);
  assert.deepEqual(writes, ["/api/connect-arm","/operator/connect-camera"]);
  assert.equal(button.textContent, "Equipo conectado");
  assert.equal(button.disabled, true);
});
test("a connected device is skipped and a partial connection can be retried", async () => {
  const {node,writes} = await openDashboard({arm:false,camera:false,bridge:false}, true);
  await node("connect-all").handlers.click();
  assert.deepEqual(writes, ["/api/connect-arm","/operator/connect-camera"]);
  assert.match(node("feedback").textContent,/Brazo MKS/);
  assert.equal(node("connect-all").disabled,false);
  await node("connect-all").handlers.click();
  assert.deepEqual(writes, ["/api/connect-arm","/operator/connect-camera","/api/connect-arm"]);
});

test("arm diagnostics distinguish a visible but silent board from a missing USB cable", async () => {
  for (const [code, message] of [["arm_no_reply", "12 V"], ["arm_usb_missing", "cable USB"]]) {
    const {node,writes} = await openDashboard({arm:false,camera:true,bridge:true}, code);
    await node("arm-btn").handlers.click();
    assert.ok(node("feedback").textContent.includes(message));
    assert.deepEqual(writes, ["/api/connect-arm"]);
  }
});

test("a recovered arm clears its previous error during read-only polling", async () => {
  const hardware = {arm:false,camera:true,bridge:true};
  const {node, writes, poll} = await openDashboard(hardware, "arm_no_reply");
  await node("arm-btn").handlers.click();
  assert.equal(node("feedback").hidden, false);
  hardware.arm = true;
  await poll();
  assert.equal(node("feedback").hidden, true);
  assert.equal(node("arm-state").textContent, "Conectado");
  assert.deepEqual(writes, ["/api/connect-arm"]);
});
