# Kit Readiness judge demo script

**Track 1 · Make a legacy app agent-ready**  
**Run time · 3 minutes 30 seconds, including clicks and pauses**

## Before the timer starts

Open the planner at `http://127.0.0.1:8420/`. Set **Arduino Workshop Kit**, **Lab A**, **30**, and **June 14, 2030**. Keep the form visible. In a second window or tab, open the completed agent conversation for the June 14 scenario with its tool calls ready to expand. Use the three main planner buttons during the pitch.

## 0:00–0:25 · Set up the problem

**Show** the planner form. Point to **Lab A**, **30**, and the **Needed by** date as you speak.

**You should see** Arduino Workshop Kit selected, with 30 kits due June 14.

**Say**

> “Imagine you’re running an Arduino workshop for 30 people this Friday. Some parts are in Lab A, some are in a storeroom, and some are on purchase orders. Before you order anything, can you tell how many kits you can build and what’s actually missing? That’s what Kit Readiness does with the inventory already in InvenTree.”

## 0:25–0:50 · Check readiness

**Show** the result of clicking **Check readiness**. Point to the result heading, then the **Arduino Uno** row.

**You should see** **18 kits buildable today**, **12 kits short on site**, and **Arduino Uno** listed as the limiting component. The board row shows **30 required** and **18 on site**.

**Say**

> “Lab A can build 18 complete kits today. We need one Arduino Uno per kit, and we have 18 boards here. We have enough USB cables, but without more boards we’re 12 kits short.”

## 0:50–1:20 · Find stock to transfer

**Show** the result of clicking **Plan transfers**. Scroll to **Suggested transfers**, then point back to the **After transfers** column.

**You should see** moves from **Annex Storeroom** to **Lab A** for **8 Arduino Uno boards** and **2 temperature sensors**. The board and sensor rows each show **4** under **After transfers**.

**Say**

> “The Annex Storeroom has eight boards and two temperature sensors we can move to Lab A. If the coordinator makes both moves, the remaining shortage is four boards and four sensors. Before buying those, let’s check what’s already on order.”

## 1:20–2:00 · Draft the purchase

**Show** the result of clicking **Draft purchase list**. Point to the two entries under **Open purchase orders**, then to **Suggested purchase** in the table.

**You should see** **PO-1001**, three sensors due June 12, counted toward the shortfall. **PO-1002**, ten boards due June 17, says **Arrives after workshop**. The purchase column shows **4 boards**, **1 sensor**, and **0 cables**.

**Say**

> “Three sensors are due June 12, so they cover three of the four we still need. There are ten boards on order, but they arrive three days after the workshop. For June 14, the draft says to buy four boards and one sensor.”

## 2:00–2:30 · Change the deadline live

**Show** the **Needed by** field. Change it to **June 17, 2030**, click **Draft purchase list** again, then point to the Arduino Uno purchase quantity.

**You should see** the board purchase drop from **4** to **0**. PO-1002 now shows **4 counted toward the shortfall**. The sensor purchase stays at **1**, and the heading still shows **18 kits buildable today**.

**Say**

> “What if the workshop moves to Monday? The same order now arrives in time to cover the four boards we were missing. The draft drops to one sensor. We can still build 18 today. What changed is what we need to buy by the deadline.”

## 2:30–3:15 · Show Synapse and the agent

**Show** **Synapse tool calls** under the planner result. Point to `get_bill_of_materials`, `get_component_stock`, and `get_incoming_stock`. Switch to the completed agent run and scroll through its three replies. Expand a tool call from the purchasing reply.

**You should see** tool names and record counts in the planner, then the agent’s three June 14 answers with tool activity. Its purchase answer should still be **4 boards and 1 sensor** for the original Friday deadline.

**Say**

> “Here are the inventory reads behind that result. Synapse Auto generated five read-only MCP tools from a small adapter over InvenTree’s existing API. Assemblies and locations identify the job, the bill of materials and stock tell us what we can build or move, and open orders tell us what arrives in time. Here’s the agent run for the original Friday deadline. It used those same tools to check readiness, find transfers, and draft the purchase.”

## 3:15–3:30 · Close

**Show** the agent’s Friday purchase answer and leave it visible.

**You should see** the final quantities and the reason the board order arrives too late.

**Say**

> “That’s one workflow from stockroom to purchase draft. The coordinator gets a build count, a transfer list, and a buying decision tied to the workshop date. InvenTree stays the source of truth.”

## Agent run for Track 1

Track 1 asks for an agent completing at least three real tasks through a Synapse Auto-generated MCP server while leaving the original application code intact. The bundled planner is a deterministic Python MCP client. Use a separate agent client to demonstrate that a model can discover and use the same tools. Keep its successful run visible for the timed pitch and rerun a task live if the judges ask.

With the inventory adapter running on port 8410, configure a local stdio MCP server using the repo’s `.venv/Scripts/python.exe` as the command and the absolute path to `synapse_auto_server.py` as its sole argument. Set `ENDPOINT_BASE_URL=http://127.0.0.1:8410` in the server environment. The agent client must run on the demo machine or have a connection to that local MCP server.

Run these in order in one conversation. Keep the expected answers offscreen while prompting.

1. **Readiness.** “Use the Kit Readiness MCP tools. I’m running a workshop for 30 people at Lab A on June 14, 2030. How many Arduino Workshop Kits can I build there today, and which part limits that number? Use the bill of materials and available stock after allocations.” Expect **18, limited by Arduino Uno**.
2. **Transfers.** “Check stock at other locations. What can I move to Lab A to get closer to 30 kits, and what would still be missing after the moves? Give me quantities and the source location.” Expect **8 boards and 2 sensors from Annex Storeroom**, leaving **4 boards and 4 sensors** short.
3. **Purchasing.** “For that same June 14 deadline, check placed purchase orders and draft the remaining purchase list after the suggested moves. Count only outstanding quantities due at Lab A by the deadline. Show which orders you counted or excluded and why.” Expect **4 boards and 1 sensor**. PO-1001 contributes **3 sensors**. PO-1002 arrives late.

## Rehearsal and fallback

- Follow [Quick start](README.md#quick-start). Verify ports **8400** (InvenTree), **8410** (inventory adapter), and **8420** (planner). Reset the planner date to June 14 after any rehearsal.
- Check that the timed sequence gives **18 on site**, **8 boards and 2 sensors to move**, and **4 boards and 1 sensor to buy**. If the stock has been edited, check the source record quantities. The seed script creates missing records and preserves existing quantities.
- Keep a successful agent run open with tool activity visible. Save a local recording of the successful run and the deadline change for a connectivity failure. If you switch to the recording, identify it as a rehearsal and pick up at the step you were showing.
- The deadline change is the default live proof. For a source-data check during Q&A, use the seeded demo inventory and change the Lab A Arduino Uno stock from **18 to 30** in InvenTree, then click **Check readiness** again. Expect **24 kits**, limited by temperature sensors. Restore the board quantity to **18** afterward.

## Judge questions

**What did Synapse generate?** A local MCP server exposing five read-only HTTP routes from a thin FastAPI adapter over InvenTree’s existing REST API. InvenTree runs from its published image. The repo contains the adapter, the generated server, and the rebuild script. See [inventory_api.py](inventory_api.py), [synapse_auto_server.py](synapse_auto_server.py), and [rebuild-mcp.py](rebuild-mcp.py).

**Where does the reliability come from?** In the planner, Python computes capacity from the fixed, single-level bill of materials and stock after allocations. It deducts suggested transfers, then counts outstanding orders due at the assembly location by the requested date. The tool trace shows calls and record counts. See [planner.py](planner.py).

**Can it place an order or move stock?** The exposed tools are read-only. The transfer quantities and purchase list are drafts the coordinator can review and act on.
