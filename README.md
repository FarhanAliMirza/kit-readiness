# Kit Readiness

A Vibe-a-thon Track 1 demo. A lab coordinator can check how many workshop kits can be assembled, find missing components in other storerooms, and draft a purchase list. The planner uses live InvenTree inventory through a Synapse-generated MCP server. It runs locally without an AI API key.

## Run the demo

Use Python 3.12+ and Docker Compose. These examples use PowerShell. On macOS or Linux, use `.venv/bin/python` in place of `.venv/Scripts/python.exe`.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
docker compose up -d
```

Wait for the InvenTree web server at <http://127.0.0.1:8400/api/> to return its version. The first launch runs database migrations. Then collect the original InvenTree UI's assets and seed the demo data through its API.

```powershell
docker compose exec -T inventree invoke static
.venv/Scripts/python.exe seed_demo.py
```

Run these in separate terminals and open <http://127.0.0.1:8420>.

```powershell
.venv/Scripts/python.exe -m uvicorn inventory_api:app --host 127.0.0.1 --port 8410
.venv/Scripts/python.exe -m uvicorn web_app:app --host 127.0.0.1 --port 8420
```

The original InvenTree UI is at <http://127.0.0.1:8400>. Sign in to the loopback-only demo with username `kit-demo` and password `kit-readiness-local-demo`. For a different InvenTree instance, set `INVENTREE_URL` and `INVENTREE_TOKEN` in the adapter's environment and give the token read permission for the data below. The demo seed requires the included local admin account and is intended for the bundled instance.

## Three demo tasks

Select **Arduino Workshop Kit**, **Lab A**, **30 kits**, and **June 14, 2030**.

| Action | Expected output on the seed data |
| --- | --- |
| Check readiness | 18 kits are buildable now. Arduino Uno boards are the limiting component. |
| Plan transfers | Move 8 boards and 2 temperature sensors from Annex Storeroom. |
| Draft purchase list | Buy 4 boards and 1 temperature sensor. Three sensors from PO-1001 count toward the deadline. The ten boards on PO-1002 arrive too late. |

Expand **Synapse tool calls** to see which reads each task used. To demonstrate live data, open the Arduino Uno stock item at Lab A in InvenTree and add 12 boards using its stock adjustment action. Rerun **Check readiness**. Capacity rises from 18 to 24, with temperature sensors now limiting the build. Set that stock item back to 18 for the next run.

## Synapse integration

`Planner → Synapse MCP over stdio → read-only FastAPI adapter → InvenTree REST API`

Synapse CLI 0.1.9 did not discover InvenTree's Django class-based routes directly. The adapter declares five routes that forward reads to the existing API. The original InvenTree image and application code are used as published. The planner reads inventory only through the generated tools.

| Tool | Used for |
| --- | --- |
| `list_assemblies` | Select an existing active assembly. |
| `list_locations` | Resolve the assembly location and transfer sources. |
| `get_bill_of_materials` | Get the required quantity of each component. |
| `get_component_stock` | Check usable stock and subtract sales/build allocations. |
| `get_incoming_stock` | Compare placed purchase order balances, destinations, and arrival dates against the deadline. |

The demo agent follows three predefined workflows with exact quantity calculations. It handles fixed-quantity, single-level bills of materials and specific stock locations. Suggested transfers and purchases are drafts displayed on screen. Incoming stock counts only when it is outstanding, dated by the deadline, and destined for the selected location. Stock and order availability are read live when each task runs.

The generated server is committed as `synapse_auto_server.py`. To regenerate it, install Node.js 20+ and run `python rebuild-mcp.py`. The CLI uses local Auto mode with smart naming disabled. This invocation needs neither an Ollama process nor a provider key.

To use the generated tools from another MCP client, point its stdio configuration at the virtual environment's Python, pass the absolute path to `synapse_auto_server.py`, and set `ENDPOINT_BASE_URL` to `http://127.0.0.1:8410`. Keep the adapter running as shown above.
