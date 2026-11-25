import { startDemo } from "./tours.js";

const byId = (id) => document.getElementById(id);
const form = byId("plan-form");
const inputs = byId("inputs");
const demoControls = byId("demo-controls");
const results = byId("results");
const status = byId("status");
const number = new Intl.NumberFormat(undefined, { maximumFractionDigits: 6 });
const format = (value) => number.format(Number(value));

function element(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

function announce(message, error = false) {
  status.textContent = message;
  status.classList.toggle("error", error);
}

async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "The planner could not complete this request.");
  }
  return data;
}

function populate(id, rows, preferred) {
  const select = byId(id);
  select.replaceChildren(...rows.map((row) => {
    const option = element("option", row.name);
    option.value = row.id;
    option.selected = row.name === preferred;
    return option;
  }));
}

function appendList(container, id, heading, items, empty) {
  const group = element("section");
  group.id = id;
  group.className = "detail-group";
  group.append(element("h3", heading));
  if (items.length) {
    const list = element("ul");
    list.append(...items.map((item) => element("li", item)));
    group.append(list);
  } else {
    group.append(element("p", empty));
  }
  container.append(group);
}

function drawTable(plan) {
  const columns = [
    ["Component", (row) => row.name],
    ["Per kit", (row) => format(row.per_kit)],
    ["Required", (row) => format(row.required)],
    ["On site", (row) => format(row.onsite)],
    ["Short on site", (row) => format(row.shortage)],
  ];
  if (plan.workflow !== "readiness") {
    columns.push(["After transfers", (row) => format(row.after_transfers)]);
  }
  if (plan.workflow === "purchase") {
    columns.push(["Suggested purchase", (row) => format(row.purchase)]);
  }
  const table = element("table");
  const head = table.createTHead().insertRow();
  for (const [title] of columns) {
    const cell = element("th", title);
    cell.scope = "col";
    head.append(cell);
  }
  const body = table.createTBody();
  for (const component of plan.components) {
    const row = body.insertRow();
    for (const [, value] of columns) {
      row.insertCell().textContent = value(component);
    }
  }
  byId("table-wrap").replaceChildren(table);
}

function drawPlan(plan) {
  const short = plan.capacity < plan.requested;
  byId("result-title").textContent = `${format(plan.capacity)} kits buildable today`;
  byId("result-description").textContent =
    `${plan.kit} · ${plan.location} · ${format(plan.requested)} needed by ${plan.needed_by}. ` +
    `Limiting components: ${plan.limiting.join(", ")}.`;
  const badge = byId("result-state");
  badge.className = short ? "short" : "ready";
  badge.textContent = short ? `${format(plan.requested - plan.capacity)} kits short on site` : "Ready on site";
  drawTable(plan);

  const details = byId("details");
  details.replaceChildren();
  if (plan.workflow !== "readiness") {
    const transfers = plan.components.flatMap((row) => row.transfers.map(
      (transfer) => `Move ${format(transfer.quantity)} × ${row.name} from ${transfer.from} to ${plan.location}.`,
    ));
    appendList(details, "suggested-transfers", "Suggested transfers", transfers, "No transfers are available or needed.");
  }
  if (plan.workflow === "purchase") {
    const inbound = plan.components.flatMap((row) => row.inbound.map((order) => {
      const explanation = order.reason || `${format(order.counted)} counted toward the shortfall`;
      return `${order.reference} · ${format(order.outstanding)} × ${row.name} · ${order.date || "Date unknown"} · ${explanation}.`;
    }));
    appendList(details, "open-orders", "Open purchase orders", inbound, "There are no outstanding placed orders for these components.");
  }

  byId("trace-list").replaceChildren(...plan.trace.map((call) => {
    const args = call.part_id ? ` (part #${call.part_id})` : "";
    return element("li", `${call.tool}${args} · ${call.records} records`);
  }));
  results.hidden = false;
}

async function runPlan(workflow) {
  const values = {
    workflow,
    kit_id: Number(byId("kit").value),
    location_id: Number(byId("location").value),
    kits: Number(byId("kits").value),
    needed_by: byId("needed-by").value,
  };
  inputs.disabled = true;
  demoControls.disabled = true;
  results.hidden = true;
  announce("Checking live inventory through Synapse…");
  try {
    const plan = await request("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });
    drawPlan(plan);
    announce("");
    return true;
  } catch (error) {
    announce(error.message, true);
    return false;
  } finally {
    inputs.disabled = false;
    demoControls.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runPlan(event.submitter?.value || "readiness");
});

byId("start-demo").addEventListener("click", () => {
  if (form.reportValidity()) startDemo(byId("demo-workflow").value, runPlan);
});

async function initialize() {
  try {
    const catalog = await request("/api/catalog");
    if (!catalog.kits.length || !catalog.locations.length) {
      throw new Error("Add a kit and a stock location in InvenTree, then reload this page.");
    }
    populate("kit", catalog.kits, "Arduino Workshop Kit");
    populate("location", catalog.locations, "Lab A");
    await runPlan("readiness");
  } catch (error) {
    announce(error.message, true);
  }
}

initialize();
