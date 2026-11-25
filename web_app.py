from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from planner import InvalidRequest, build_plan, catalog, open_inventory

app = FastAPI(title="Kit Readiness")
static = Path(__file__).with_name("static")
app.mount("/static", StaticFiles(directory=static), name="static")


class PlanRequest(BaseModel):
    kit_id: Annotated[int, Field(gt=0)]
    location_id: Annotated[int, Field(gt=0)]
    kits: Annotated[int, Field(gt=0, le=10_000)]
    needed_by: date
    workflow: Literal["readiness", "transfer", "purchase"]


async def run(workflow):
    # Capture workflow errors inside the stdio context so they are not wrapped
    # in the transport's task-group exception on shutdown.
    async with open_inventory() as tools:
        try:
            result = await workflow(tools)
        except (InvalidRequest, RuntimeError) as exc:
            result = exc
    if isinstance(result, InvalidRequest):
        raise HTTPException(422, str(result))
    if isinstance(result, RuntimeError):
        raise HTTPException(502, str(result))
    return result


@app.get("/")
def index():
    return FileResponse(static / "index.html")


@app.get("/api/catalog")
async def get_catalog():
    return await run(catalog)


@app.post("/api/plan")
async def plan(request: PlanRequest):
    return await run(lambda tools: build_plan(tools, **request.model_dump()))
