# Kit Readiness

Kit Readiness helps workshop coordinators find out how many kits they can assemble today, locate spare components in other storerooms, and draft a purchase list for the remaining shortfall. The planner reads live [InvenTree](https://inventree.org/) inventory through a Synapse-generated MCP server. It runs locally without an AI API key.

Built for Vibe-a-thon Track 1.

## Quick start

You need Python 3.12+ and Docker with Compose v2. Run the commands from the repository root. On macOS or Linux, replace `.venv/Scripts/python.exe` with `.venv/bin/python`.

1. Install the Python dependencies and start the bundled InvenTree instance.

   ```powershell
   python -m venv .venv
   .venv/Scripts/python.exe -m pip install -r requirements.txt
   docker compose up -d
   ```

2. Wait for the [InvenTree API](http://127.0.0.1:8400/api/) to return version information. The first launch runs database migrations. Collect the InvenTree web UI assets and seed the workshop inventory.

   ```powershell
   docker compose exec -T inventree invoke static
   .venv/Scripts/python.exe seed_demo.py
   ```

3. Start the inventory adapter and the planner in separate terminals.

   ```powershell
   .venv/Scripts/python.exe -m uvicorn inventory_api:app --host 127.0.0.1 --port 8410
   ```

   ```powershell
   .venv/Scripts/python.exe -m uvicorn web_app:app --host 127.0.0.1 --port 8420
   ```

4. Open the [workshop kit planner](http://127.0.0.1:8420/). To inspect or edit the source inventory, open [InvenTree](http://127.0.0.1:8400/) and sign in with the bundled local demo account, `kit-demo` / `kit-readiness-local-demo`.

Stop the Python servers with `Ctrl+C`. Run `docker compose down` to stop the containers and retain the demo inventory in the named volume.

## Guided demos

Use **Arduino Workshop Kit**, **Lab A**, **30 kits**, and **June 14, 2030** to reproduce the results below. Pick a **Guided demo**, select **Start demo**, and choose **Run plan** when prompted. Each walkthrough uses the current form values and finishes by opening **Synapse tool calls**. You can also run the three workflows directly from the form.

| Guided demo | Expected result with the seed data |
| --- | --- |
| **Kit readiness** | Lab A can build 18 kits today. Arduino Uno boards are the limiting component. |
| **Stock transfers** | Move 8 Arduino Uno boards and 2 temperature sensors from Annex Storeroom to Lab A. |
| **Purchase planning** | After transfers and eligible incoming stock, buy 4 Arduino Uno boards and 1 temperature sensor. The 3 sensors on PO-1001 arrive in time. The 10 boards on PO-1002 arrive after the deadline. |

To see a live inventory change, add 12 boards to the Arduino Uno stock item at Lab A in InvenTree, then run **Check readiness** again. Capacity rises to 24 kits and temperature sensors become the limiting component. Restore the board quantity to 18 to reproduce the original demo. The seed script creates missing demo records and preserves existing stock quantities.

## How it works

The browser calls `GET /api/catalog` for the form options and `POST /api/plan` for the selected workflow. The Python planner opens a Synapse MCP session over stdio. The generated server forwards tool calls to the read-only FastAPI adapter, which reads the InvenTree REST API.

| Synapse tool | Inventory data |
| --- | --- |
| `list_assemblies` | Active kit assemblies |
| `list_locations` | Assembly locations and potential transfer sources |
| `get_bill_of_materials` | Required components and quantities per kit |
| `get_component_stock` | Usable stock and allocations at each location |
| `get_incoming_stock` | Placed purchase order lines, quantities, destinations, and expected dates |

The planner supports fixed-quantity, single-level bills of materials and calculates capacity from usable stock after allocations at the selected location. The purchase workflow subtracts suggested transfers first, then counts outstanding stock that is due by the deadline at that location. Transfers and purchases are drafts for the coordinator to review.

## Configuration

| Variable | Set for | Purpose |
| --- | --- | --- |
| `INVENTREE_URL` | Inventory adapter | Base URL of the InvenTree instance. Defaults to `http://127.0.0.1:8400`. |
| `INVENTREE_TOKEN` | Inventory adapter | API token with read access to parts, bills of materials, stock, stock locations, and purchase orders. When unset, the adapter uses the bundled demo credentials. |
| `ENDPOINT_BASE_URL` | Planner or standalone MCP server | Inventory adapter URL. The planner defaults to `http://127.0.0.1:8410` and passes the value to the generated server. |

For a separate InvenTree instance, set `INVENTREE_URL` and `INVENTREE_TOKEN` before starting the adapter. Run the seed script against the bundled local demo inventory for the sample data above.

## Repository guide

| Path | Role |
| --- | --- |
| [`web_app.py`](web_app.py) and [`static/`](static/) | Planner API, browser UI, and guided walkthroughs |
| [`planner.py`](planner.py) | MCP client and workflow calculations |
| [`inventory_api.py`](inventory_api.py) | Five read-only routes for Synapse Auto scanning |
| [`synapse_auto_server.py`](synapse_auto_server.py) | Generated MCP server used by the planner |
| [`seed_demo.py`](seed_demo.py) | Demo assembly, stock, and purchase orders |
| [`compose.yaml`](compose.yaml) and [`Caddyfile`](Caddyfile) | Bundled InvenTree instance and local reverse proxy |

The walkthrough steps live in [`static/tours.js`](static/tours.js). The app serves Driver.js 1.14.0 from [`static/vendor/driver.js/`](static/vendor/driver.js/) with its [MIT license](static/vendor/driver.js/license). The app requires no frontend build or CDN connection. [Driver.js documentation](https://driverjs.com/docs/installation)

### Regenerate the Synapse server

The generated server is checked in and ready to run. To rebuild it after changing the adapter routes, install Node.js 20+ and run `python rebuild-mcp.py`. The script pins Synapse CLI 0.1.9 and uses local Auto mode, which needs neither an Ollama process nor a provider key. The adapter exposes routes that this version of the scanner can discover in front of the published InvenTree application.

For another MCP client, configure a stdio server with the virtual environment's Python executable as the command, the absolute path to `synapse_auto_server.py` as its argument, and `ENDPOINT_BASE_URL=http://127.0.0.1:8410` in its environment. Keep the adapter running.

## Troubleshooting

- If InvenTree is still starting, check `docker compose logs --tail 50 inventree` and retry the API URL after migrations finish.
- If the planner cannot load the catalog, check the [adapter's parts endpoint](http://127.0.0.1:8410/parts). A connection error points to the adapter process. A `502` points to its InvenTree connection or credentials.
- If the kit list is empty, run the seed script for the bundled instance or check for an active assembly and a stock location in the configured instance.
