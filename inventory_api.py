"""Read-only route declarations for Synapse's Auto scanner."""

import os
from contextlib import contextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="InvenTree inventory reads")
INVENTREE_URL = os.getenv("INVENTREE_URL", "http://127.0.0.1:8400")
DEMO_LOGIN = ("kit-demo", "kit-readiness-local-demo")


@contextmanager
def inventree_client():
    token = os.getenv("INVENTREE_TOKEN")
    options = {"headers": {"Authorization": f"Token {token}"}} if token else {
        "auth": DEMO_LOGIN,
    }
    with httpx.Client(base_url=INVENTREE_URL, timeout=10, **options) as client:
        yield client


def records(client, path, **params):
    """Read all pages without following URLs supplied by the upstream API."""
    offset = 0
    while True:
        response = client.get(path, params={**params, "limit": 100, "offset": offset})
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            yield from payload
            return
        page = payload["results"]
        yield from page
        if not payload.get("next"):
            return
        if not page:
            raise ValueError("InvenTree returned an empty page with a next link.")
        offset += len(page)


@app.exception_handler(httpx.HTTPError)
async def upstream_failure(request, exc):
    status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
    message = f"InvenTree returned HTTP {status}." if status else "InvenTree is unreachable."
    return JSONResponse(status_code=502, content={"detail": message})


@app.get("/parts")
def list_assemblies():
    """List active kit assemblies with InvenTree part IDs."""
    with inventree_client() as client:
        return {"records": [
            {"id": row["pk"], "name": row["name"]}
            for row in records(client, "/api/part/", assembly="true", active="true")
        ]}


@app.get("/locations")
def list_locations():
    """List inventory locations with their InvenTree IDs."""
    with inventree_client() as client:
        return {"records": [
            {"id": row["pk"], "name": row.get("pathstring") or row["name"]}
            for row in records(client, "/api/stock/location/")
        ]}


@app.get("/bom/{part_id}")
def get_bill_of_materials(part_id: int):
    """Read the required components and quantities for an assembly."""
    with inventree_client() as client:
        result = []
        for row in records(client, "/api/bom/", part=part_id, sub_part_detail="true"):
            if row["optional"]:
                continue
            if row["consumable"] or float(row["setup_quantity"] or 0) or float(row["attrition"] or 0) or row["rounding_multiple"]:
                raise HTTPException(422, "This planner supports fixed-quantity assembly BOMs.")
            result.append({
                "id": row["pk"],
                "component": row["sub_part"],
                "name": row["sub_part_detail"]["name"],
                "quantity": row["quantity"],
            })
        return {"records": result}


@app.get("/stock/{part_id}")
def get_component_stock(part_id: int):
    """Read usable component stock, reservations, and location IDs."""
    with inventree_client() as client:
        return {"records": [
            {
                "id": row["pk"], "location": row["location"],
                "quantity": row["quantity"], "allocated": row["allocated"],
            }
            for row in records(client, "/api/stock/", part=part_id, in_stock="true")
            if row["location"] is not None and row["status"] == 10
        ]}


@app.get("/incoming/{part_id}")
def get_incoming_stock(part_id: int):
    """Read placed purchase order lines, expected dates and outstanding quantities."""
    with inventree_client() as client:
        lines = records(client, "/api/order/po-line/", internal_part=part_id)
        orders = {}
        result = []
        for line in lines:
            if line["internal_part"] != part_id:
                continue
            order_id = line["order"]
            if order_id not in orders:
                response = client.get(f"/api/order/po/{order_id}/")
                response.raise_for_status()
                orders[order_id] = response.json()
            order = orders[order_id]
            if order["status"] != 20:
                continue
            result.append({
                "id": line["pk"], "order": order_id, "reference": order["reference"],
                "date": line["target_date"] or order["target_date"],
                "destination": line["destination"] or order["destination"],
                "quantity": line["quantity"], "received": line["received"],
            })
        return {"records": result}
