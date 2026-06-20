from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .api import deliveries, vehicles, simulations
from .database import engine, Base
# Ensure all models are imported so SQLAlchemy registers them
from .models.region import Region
from .models.city import City
from .models.vehicle import Vehicle
from .models.delivery import Delivery
from .models.simulation import Simulation, Route, RouteStop

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Logistics Macro Planner")

app.include_router(deliveries.router)
app.include_router(vehicles.router)
app.include_router(simulations.router)

app.mount("/", StaticFiles(directory="backend/app/static", html=True), name="static")

@app.get("/")
def health():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    # Add the root directory to path to prevent import issues
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)

