"""Workflow orchestration over the generated Synapse MCP tools."""

import json
import os
import sys
from contextlib import asynccontextmanager
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

SERVER = Path(__file__).with_name("synapse_auto_server.py")
ZERO = Decimal(0)


@asynccontextmanager
async def open_inventory():
    config = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER)],
        env={"ENDPOINT_BASE_URL": os.getenv("ENDPOINT_BASE_URL", "http://127.0.0.1:8410")},
    )
    async with stdio_client(config) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            yield InventoryTools(session)


class InventoryTools:
    def __init__(self, session):
        self.session = session
        self.trace = []

    async def read(self, tool, part_id=None):
        args = {} if part_id is None else {"part_id": part_id}
        try:
            result = await self.session.call_tool(tool, args, read_timeout_seconds=timedelta(seconds=25))
        except McpError as exc:
            raise RuntimeError(f"{tool} could not complete. {exc}") from exc
        detail = next((item.text for item in result.content if item.type == "text"), "")
        if result.isError:
            raise RuntimeError(f"{tool} failed. {detail}")
        try:
            payload = result.structuredContent or json.loads(detail)
            rows = payload["records"]
        except (ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(f"{tool} returned an unexpected response.") from exc
        self.trace.append({"tool": tool, "part_id": part_id, "records": len(rows)})
        return rows


class InvalidRequest(ValueError):
    pass


async def catalog(tools):
    return {
        "kits": await tools.read("list_assemblies"),
        "locations": await tools.read("list_locations"),
    }


def quantity(value):
    return Decimal(str(value))


def choose(rows, record_id, label):
    record = next((row for row in rows if row["id"] == record_id), None)
    if record is None:
        raise InvalidRequest(f"Select a valid {label}.")
    return record


def transfer_plan(stock, names, home, shortage):
    transfers = []
    for location in sorted(stock, key=lambda key: (-stock[key], key)):
        amount = min(shortage, stock[location])
        if location != home and location in names and amount > 0:
            transfers.append({"from": names[location], "quantity": amount})
            shortage -= amount
    return transfers, shortage


def inbound_plan(orders, home, needed_by, shortage):
    inbound = []
    for order in sorted(orders, key=lambda row: (row["date"] or "", row["id"])):
        remaining = max(ZERO, quantity(order["quantity"]) - quantity(order["received"]))
        if not remaining:
            continue
        if order["destination"] != home:
            reason = "Different or unknown destination"
        elif not order["date"]:
            reason = "Arrival date unknown"
        elif date.fromisoformat(order["date"]) > needed_by:
            reason = "Arrives after workshop"
        else:
            reason = ""
        counted = ZERO if reason else min(shortage, remaining)
        shortage -= counted
        inbound.append({**order, "outstanding": remaining, "counted": counted, "reason": reason})
    return inbound, shortage


async def build_plan(tools, *, kit_id, location_id, kits, needed_by, workflow):
    options = await catalog(tools)
    kit = choose(options["kits"], kit_id, "kit")
    location = choose(options["locations"], location_id, "location")
    names = {row["id"]: row["name"] for row in options["locations"]}
    bom = await tools.read("get_bill_of_materials", kit_id)
    if not bom:
        raise InvalidRequest("This kit has no required components in InvenTree.")

    components = {}
    for line in bom:
        component = components.setdefault(line["component"], {
            "name": line["name"], "per_kit": ZERO, "bom_ids": [],
        })
        component["per_kit"] += quantity(line["quantity"])
        component["bom_ids"].append(line["id"])

    rows = []
    for part_id, component in components.items():
        per_kit = component["per_kit"]
        if per_kit <= 0:
            raise InvalidRequest(f"{component['name']} has an invalid BOM quantity.")
        stock_items = await tools.read("get_component_stock", part_id)
        stock = {}
        for item in stock_items:
            key = item["location"]
            free = max(ZERO, quantity(item["quantity"]) - quantity(item["allocated"]))
            stock[key] = stock.get(key, ZERO) + free
        onsite = stock.get(location_id, ZERO)
        required = per_kit * kits
        shortage = max(ZERO, required - onsite)
        row = {
            **component, "part_id": part_id, "required": required, "onsite": onsite,
            "shortage": shortage, "capacity": int(onsite // per_kit),
            "stock_ids": [item["id"] for item in stock_items],
        }
        if workflow in ("transfer", "purchase"):
            transfers, shortage = transfer_plan(stock, names, location_id, shortage)
            row.update(transfers=transfers, after_transfers=shortage)
        if workflow == "purchase":
            inbound, shortage = inbound_plan(
                await tools.read("get_incoming_stock", part_id), location_id, needed_by, shortage,
            )
            row.update(inbound=inbound, purchase=shortage)
        rows.append(row)

    capacity = min(row["capacity"] for row in rows)
    return {
        "kit": kit["name"], "location": location["name"], "requested": kits,
        "needed_by": needed_by, "capacity": capacity,
        "limiting": [row["name"] for row in rows if row["capacity"] == capacity],
        "workflow": workflow, "components": rows, "trace": tools.trace,
    }
