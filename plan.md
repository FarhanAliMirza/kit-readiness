# Kit Readiness app plan

## Goal

Help a workshop coordinator turn a kit count, assembly location, and deadline into three decisions: how many kits can be assembled today, which parts to move from other locations, and what to buy for the remaining shortfall. Kit Readiness uses live InvenTree data through Synapse Auto for Vibe-a-thon Track 1.

## User workflow

| Step | What the app does | What the coordinator gets |
| --- | --- | --- |
| **Check readiness** | Read the bill of materials and usable on-site stock after allocations. Divide each component's stock by its per-kit requirement and take the lowest whole-kit capacity. | Buildable kits today, limiting components, and shortages by part. |
| **Plan transfers** | Look for usable stock at other locations and suggest moves up to each part's shortage. | A draft with the part, quantity, source, destination, and shortage after transfers. |
| **Draft purchase list** | Deduct suggested transfers, then credit outstanding quantities on placed orders due at the assembly location by the deadline. | Purchase quantities and explanations for which orders count. |

## Implementation

- **Planner UI and API.** [web_app.py](web_app.py) serves the picker, three actions, results table, and Synapse tool trace. The UI also includes guided walkthroughs for rehearsal.
- **Workflow logic.** [planner.py](planner.py) computes all three plans and calls the MCP server over stdio. The current scope is fixed-quantity, single-level bills of materials.
- **Inventory integration.** [inventory_api.py](inventory_api.py) exposes five read-only routes for assemblies, locations, bills of materials, stock by location, and incoming orders. [synapse_auto_server.py](synapse_auto_server.py) is the generated MCP server. The adapter reads the existing InvenTree REST API, and InvenTree runs from its published image.
- **Local demo data.** [seed_demo.py](seed_demo.py) provides the Arduino kit, Lab A and Annex stock, and two purchase orders. Follow the [quick start](README.md#quick-start) to run the stack. The coordinator reviews the transfer and purchase drafts.

## Acceptance checks

Use **Arduino Workshop Kit**, **Lab A**, **30 kits**, and **June 14, 2030**.

| Check | Expected result |
| --- | --- |
| Readiness | **18 kits buildable today**, limited by Arduino Uno boards. |
| Transfers | **8 boards and 2 temperature sensors** from Annex Storeroom, leaving **4 boards and 4 sensors** short. |
| Purchases | **4 boards and 1 sensor**. PO-1001 contributes 3 sensors. PO-1002 arrives after the deadline. |
| Deadline change | On **June 17**, PO-1002 covers the board shortfall and the draft drops to **1 sensor**. Today's build capacity stays at **18**. |

## Hackathon completion

1. Verify the four acceptance checks on the seeded stack. The local planner and all five MCP tools have passed the live checks.
2. Rehearse the three tasks in a separate model-driven agent client connected to the generated MCP server. Confirm the answers match the planner and the agent's tool calls are visible.
3. Submit the repository and generated MCP configuration with the three-task walkthrough. Use [script.md](script.md) for the 3-minute, 30-second judge demo.
