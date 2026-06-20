<div align="center">
  <h1>Logistics Macro Planner</h1>
  <p><strong>Pre-TMS Route Optimization Engine</strong></p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python" alt="Python 3.12+" />
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/SQLAlchemy-2.0-red" alt="SQLAlchemy" />
    <img src="https://img.shields.io/badge/NetworkX-3.0-2C2C2C" alt="NetworkX" />
    <img src="https://img.shields.io/badge/tests-16_passing-green" alt="16 tests passing" />
  </p>
</div>

## Overview

A logistics planning engine that simulates intelligent delivery consolidation across vehicles, optimizing routes by cost, distance, and plausibility. Designed as a **pre-TMS** macro planner — evaluate scenarios before they reach a real-time Transportation Management System.

## Features

- **Smart Consolidation** — First-Fit Decreasing (FFD) bin packing algorithm allocates deliveries into vehicles respecting weight, volume, and dimensional constraints
- **Route Plausibility Scoring** — Multi-factor route quality score (0-130) evaluating progression, outliers, spread, detours, and direction changes
- **Scenario Generation** — Hierarchical clustering by geographic proximity with combinatorial permutations (max 6 stops per route)
- **Vehicle Compatibility Check** — Three-tier compatibility (ok / warn / fail) for weight, volume, and dimensions
- **CSV Bulk Import** — Flexible header mapping (Portuguese/English), BOM-safe UTF-8, per-row validation
- **Route Split Recommendation** — Detects when removing a distant outlier improves the route score
- **SLA Validation** — Checks route distance against delivery deadlines (600 km/day average)
- **Interactive Dashboard** — Dark-mode glassmorphism UI with Leaflet.js map visualization
- **Simulation History** — Full persistence of scenarios, routes, stops with many-to-many relationships

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+, FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (declarative) |
| Database | SQLite (dev) / PostgreSQL (production) |
| Algorithms | NetworkX, NumPy, Pandas |
| Frontend | Vanilla HTML/CSS/JS + Leaflet.js |
| Testing | pytest (16 tests) |
| Deployment | PM2 + Cloudflare Tunnel |

## API Endpoints

### Deliveries

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/deliveries/` | List all deliveries |
| POST | `/deliveries/` | Create a delivery |
| POST | `/deliveries/upload-csv` | Bulk import via CSV |
| GET | `/deliveries/template-csv` | Download sample CSV |
| DELETE | `/deliveries/{id}` | Remove a delivery |

### Vehicles

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/vehicles/` | List vehicles |
| POST | `/vehicles/` | Create a vehicle |
| PUT | `/vehicles/{id}` | Update a vehicle |
| DELETE | `/vehicles/{id}` | Remove a vehicle |
| PATCH | `/vehicles/{id}/toggle` | Activate/deactivate |

### Simulations

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/simulations/run` | Run full simulation pipeline |
| GET | `/simulations/` | List simulation history |
| GET | `/simulations/{id}` | Simulation details |
| DELETE | `/simulations/{id}` | Remove a simulation |

## Simulation Pipeline

```
POST /simulations/run
  ↓
1. Scenario Generation (clustering + combinations)
  ↓
2. Vehicle Compatibility Filtering
  ↓
3. SLA Validation
  ↓
4. Plausibility Scoring (0-130)
  ↓
5. Optimization & Best Pick
  ↓
6. Consolidation (FFD Bin Packing)
  ↓
7. Split Recommendation
  ↓
Response: best_scenario + consolidation + split_recommendation
```

## Getting Started

```bash
# Clone and enter directory
cd logistics_macro_planner

# Install dependencies
pip install -r requirements.txt

# Run
python3 run.py
```

Access the dashboard at `http://127.0.0.1:8000` and API docs at `http://127.0.0.1:8000/docs`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./logistics.db` | Database connection URL |

## Testing

```bash
pytest -v tests/
```

16 tests covering: Haversine distance, plausibility scoring, scenario generation, volume calculation, vehicle compatibility, FFD consolidation, and edge cases.

## Project Structure

```
logistics_macro_planner/
├── backend/app/
│   ├── api/           # FastAPI route handlers
│   ├── models/        # SQLAlchemy models
│   ├── services/      # Business logic (consolidation, plausibility, optimization)
│   ├── utils/         # Geo utilities (Haversine)
│   ├── static/        # Frontend (HTML/CSS/JS + Leaflet)
│   └── main.py        # FastAPI app
├── database/          # Schema + seed data
├── samples/           # CSV examples
├── scripts/           # Migration tools
└── tests/             # pytest suite
```

## License

MIT
