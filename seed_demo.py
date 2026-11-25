"""Create the demo inventory via the original InvenTree API."""

from inventory_api import inventree_client, records

WORKSHOP_DATE = "2030-06-14"


def post(client, path, data):
    response = client.post(path, json=data)
    if response.is_error:
        raise RuntimeError(f"POST {path}: {response.status_code} {response.text}")
    return response.json() if response.content else None


def ensure(client, path, key, data, **filters):
    existing = next((row for row in records(client, path, **filters)
                     if all(row.get(field) == data[field] for field in key)), None)
    return existing or post(client, path, data)


def seed(client):
    lab, annex = [
        ensure(client, "/api/stock/location/", ["name"], {"name": name})["pk"]
        for name in ("Lab A", "Annex Storeroom")
    ]
    kit = ensure(client, "/api/part/", ["IPN"], {
        "name": "Arduino Workshop Kit", "IPN": "KR-KIT",
        "description": "Assembly for the workshop readiness demo",
        "assembly": True, "active": True,
    })["pk"]
    supplier = ensure(client, "/api/company/", ["name"], {
        "name": "Workshop Components", "is_supplier": True,
    })["pk"]
    components = {}
    for code, name, per_kit, lab_stock, annex_stock in (
        ("BOARD", "Arduino Uno", 1, 18, 8),
        ("USB", "USB Cable", 2, 100, 0),
        ("SENSOR", "Temperature Sensor", 1, 24, 2),
    ):
        part = ensure(client, "/api/part/", ["IPN"], {
            "name": name, "IPN": f"KR-{code}", "description": "Workshop component",
            "component": True, "purchaseable": True, "active": True,
        })["pk"]
        ensure(client, "/api/bom/", ["part", "sub_part"], {
            "part": kit, "sub_part": part, "quantity": per_kit,
        }, part=kit)
        for location, quantity in ((lab, lab_stock), (annex, annex_stock)):
            if quantity:
                ensure(client, "/api/stock/", ["part", "location", "batch"], {
                    "part": part, "location": location, "quantity": quantity,
                    "batch": f"KR-{code}-{location}",
                }, part=part, location=location)
        components[code] = ensure(client, "/api/company/part/", ["SKU", "supplier"], {
            "part": part, "supplier": supplier, "SKU": f"KR-{code}",
        }, part=part, supplier=supplier)["pk"]

    for reference, code, quantity, arrival in (
        ("PO-1001", "SENSOR", 3, "2030-06-12"),
        ("PO-1002", "BOARD", 10, "2030-06-17"),
    ):
        order = ensure(client, "/api/order/po/", ["reference"], {
            "reference": reference, "supplier": supplier, "target_date": arrival,
            "destination": lab, "description": "Kit Readiness demo purchase order",
        })
        ensure(client, "/api/order/po-line/", ["part", "order"], {
            "order": order["pk"], "part": components[code], "quantity": quantity,
            "target_date": arrival, "destination": lab,
        }, order=order["pk"])
        if order["status"] == 10:
            post(client, f"/api/order/po/{order['pk']}/issue/", {})


if __name__ == "__main__":
    with inventree_client() as client:
        seed(client)
    print(f"Demo inventory is ready for the {WORKSHOP_DATE} workshop.")
