from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import valuation

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="Luxury Alpha")


class BagInput(BaseModel):
    model: Literal[tuple(valuation.KNOWN_MODELS)]
    size: int
    color: Literal[tuple(valuation.KNOWN_COLORS)]
    leather: Literal[tuple(valuation.KNOWN_LEATHERS)]
    hardware: Literal[tuple(valuation.KNOWN_HARDWARE)]
    year: int = Field(ge=1980, le=2035)
    condition: Literal[tuple(valuation.KNOWN_CONDITIONS)]
    price: float = Field(gt=0)


@app.get("/api/options")
def get_options():
    return {
        "models": valuation.KNOWN_MODELS,
        "sizes": valuation.KNOWN_SIZES,
        "model_sizes": valuation.MODEL_SIZES,
        "colors": valuation.KNOWN_COLORS,
        "leathers": valuation.KNOWN_LEATHERS,
        "hardware": valuation.KNOWN_HARDWARE,
        "conditions": valuation.KNOWN_CONDITIONS,
    }


@app.post("/api/valuate")
def valuate(bag: BagInput):
    result = valuation.run_valuation(bag.model_dump())
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
