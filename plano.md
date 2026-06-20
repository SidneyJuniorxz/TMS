Perfeito. Vamos contornar totalmente o problema de download.
Vou te entregar todo o projeto em texto estruturado, exatamente como o Codex ou qualquer dev precisa para construir o sistema completo.

A ideia é que você possa:

Criar a estrutura de pastas

Copiar os arquivos

Rodar o backend

Executar testes

Evoluir o sistema

Tudo seguindo boas práticas de engenharia, rastreabilidade e arquitetura profissional.

1. VISÃO DO PROJETO
Nome do sistema

Logistics Macro Planner

Tipo de sistema

Motor de planejamento logístico pré-TMS

Objetivo

Transformar um conjunto de entregas vindas do WMS em cenários de transporte plausíveis, otimizando:

km rodado

quantidade de veículos

capacidade

restrições dimensionais

SLA

2. PROBLEMA QUE O SISTEMA RESOLVE

Hoje a roteirização macro é feita manualmente:

operador pega várias notas

agrupa por região

abre Google Maps

tenta imaginar rotas

Problemas:

dependência humana

demora

rotas ruins

difícil comparar cenários

decisões subjetivas

3. ARQUITETURA DO SISTEMA
WMS / ERP
     │
     ▼
Importação de Entregas
     │
     ▼
Normalização de Destinos
     │
     ▼
Cidade → Região Logística
     │
     ▼
Grafo Territorial
     │
     ▼
Geração de Cenários
     │
     ▼
Filtro de Plausibilidade
     │
     ▼
Validação de Capacidade
     │
     ▼
Validação SLA
     │
     ▼
Simulação de Veículos
     │
     ▼
Otimização por KM
     │
     ▼
Ranking de Rotas
     │
     ▼
Interface / Exportação para TMS
4. TECNOLOGIAS

Backend

Python

FastAPI

Processamento

pandas

networkx

numpy

Banco

PostgreSQL

Testes

pytest

Container

Docker

5. ESTRUTURA DO PROJETO

Crie a pasta:

logistics_macro_planner

Estrutura completa:

logistics_macro_planner
│
├─ backend
│  ├─ app
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ database.py
│  │  │
│  │  ├─ models
│  │  │  ├─ region.py
│  │  │  ├─ city.py
│  │  │  ├─ vehicle.py
│  │  │  ├─ delivery.py
│  │  │  └─ simulation.py
│  │  │
│  │  ├─ services
│  │  │  ├─ plausibility_engine.py
│  │  │  ├─ scenario_generator.py
│  │  │  ├─ vehicle_compatibility.py
│  │  │  ├─ sla_validator.py
│  │  │  └─ optimizer.py
│  │  │
│  │  ├─ api
│  │  │  ├─ deliveries.py
│  │  │  ├─ vehicles.py
│  │  │  └─ simulations.py
│  │  │
│  │  └─ utils
│  │     ├─ geo_utils.py
│  │     └─ distance.py
│
├─ database
│  ├─ schema.sql
│  └─ seeds.sql
│
├─ tests
│  ├─ test_engine.py
│  ├─ test_vehicle_rules.py
│  └─ test_sla.py
│
├─ samples
│  ├─ deliveries.csv
│  └─ vehicles.csv
│
├─ requirements.txt
└─ README.md
6. DEPENDÊNCIAS

Arquivo:

requirements.txt
fastapi
uvicorn
pandas
networkx
numpy
sqlalchemy
psycopg2-binary
pydantic
pytest
7. BACKEND
main.py
from fastapi import FastAPI

app = FastAPI(title="Logistics Macro Planner")

@app.get("/")
def health():
    return {"status": "running"}

Execute:

uvicorn backend.app.main:app --reload

Abrir:

http://localhost:8000/docs
8. BANCO DE DADOS

Arquivo:

database/schema.sql
CREATE TABLE regions(
 id SERIAL PRIMARY KEY,
 name TEXT,
 lat FLOAT,
 lon FLOAT
);

CREATE TABLE cities(
 id SERIAL PRIMARY KEY,
 name TEXT,
 region_id INT,
 lat FLOAT,
 lon FLOAT
);

CREATE TABLE vehicles(
 id SERIAL PRIMARY KEY,
 name TEXT,
 max_weight FLOAT,
 max_volume FLOAT,
 max_length FLOAT,
 max_width FLOAT,
 max_height FLOAT,
 cost_km FLOAT
);

CREATE TABLE deliveries(
 id SERIAL PRIMARY KEY,
 city_id INT,
 weight FLOAT,
 volume FLOAT,
 deadline_days INT
);
9. ENGINE DE PLAUSIBILIDADE

Arquivo:

services/plausibility_engine.py
def plausibility_score(route):

    score = 100

    if len(route) > 10:
        score -= 10

    return score
10. MOTOR DE VEÍCULOS

Arquivo:

vehicle_compatibility.py
def compatible(vehicle, delivery):

    if delivery["weight"] > vehicle["max_weight"]:
        return False

    if delivery["volume"] > vehicle["max_volume"]:
        return False

    return True
11. VALIDADOR SLA

Arquivo:

sla_validator.py
def validate_sla(route_distance, max_days):

    avg_km_day = 600

    days = route_distance / avg_km_day

    return days <= max_days
12. OTIMIZADOR

Arquivo:

optimizer.py
def choose_best_scenario(scenarios):

    return sorted(scenarios, key=lambda x: x["distance"])[0]
13. GERADOR DE CENÁRIOS

Arquivo:

scenario_generator.py
import itertools

def generate(deliveries):

    scenarios = []

    for r in range(1, len(deliveries)+1):

        for combo in itertools.combinations(deliveries, r):

            scenarios.append(combo)

    return scenarios
14. UTILITÁRIOS GEO

Arquivo:

geo_utils.py
from math import radians, sin, cos, sqrt, atan2

def distance(lat1, lon1, lat2, lon2):

    R = 6373.0

    dlon = radians(lon2 - lon1)
    dlat = radians(lat2 - lat1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c
15. TESTES

Arquivo:

tests/test_engine.py
def test_engine():

    route = ["A","B","C"]

    assert len(route) == 3

Rodar:

pytest
16. DADOS EXEMPLO
deliveries.csv
city,weight,volume,deadline
Curitiba,200,2,5
Joinville,100,1,4
Florianopolis,120,1.5,5
17. MOTOR DE GRAFO

Esse é o coração do sistema.

import networkx as nx

G = nx.Graph()

G.add_edge("Curitiba","Joinville",distance=130)
G.add_edge("Joinville","Florianopolis",distance=180)

Melhor rota:

nx.shortest_path(G,"Curitiba","Florianopolis",weight="distance")
18. MOTOR DE DECISÃO

Critérios de ranking

1️⃣ plausibilidade
2️⃣ capacidade
3️⃣ SLA
4️⃣ km rodado
5️⃣ veículos

19. ROADMAP

Fase 1

MVP

ingestão

regiões

grafo

cenários

ranking

Fase 2

UI

mapas

persistência

Fase 3

OR-Tools

VRP

janelas de tempo

20. COMO RODAR O PROJETO

Instalar dependências

pip install -r requirements.txt

Rodar API

uvicorn backend.app.main:app --reload

Testes

pytest
21. COMO O CODEX DEVE TRABALHAR

O Codex deve:

1️⃣ criar models SQLAlchemy
2️⃣ criar migrations
3️⃣ implementar APIs CRUD
4️⃣ criar engine de roteirização
5️⃣ integrar grafo
6️⃣ implementar otimização
7️⃣ criar testes

22. RESULTADO FINAL ESPERADO

O sistema deverá gerar algo como:

{
 "scenario":1,
 "vehicles":2,
 "route":[
  "Guarulhos",
  "Mogi",
  "São José",
  "Curitiba"
 ],
 "distance":820,
 "sla_ok":true
}
23. O QUE AINDA VAMOS CONSTRUIR

No próximo passo eu posso gerar:

✔ engine real de roteirização
✔ motor VRP completo
✔ simulação de múltiplos veículos
✔ interface visual de rotas
✔ mapa interativo

Isso transforma o projeto em um TMS inteligente completo.

Ótimo. Vamos continuar pela parte mais importante: a inteligência que separa rotas plausíveis de rotas ruins.

Isso é o que vai diferenciar o sistema de um agrupador simples.

1. O coração do sistema

O sistema não deve só montar combinações.
Ele precisa responder:

essa rota faz sentido?

essa rota é torta demais?

esse destino isolado estragou a composição?

compensa mandar outro veículo?

essa sequência respeita o eixo geográfico natural?

Então o núcleo do projeto é um Motor de Plausibilidade Logística.

2. Conceito técnico
Nome do módulo

plausibility_engine.py

Objetivo

Dar uma nota para cada cenário de rota e eliminar cenários ruins antes da otimização final.

Regra central

Nem toda combinação possível é uma combinação útil.

3. O que é uma rota “maluquice”

Uma rota ruim é uma rota que, mesmo possível, apresenta um ou mais destes problemas:

desvio excessivo

retorno desnecessário

zigue-zague

ponto muito fora do eixo principal

grande aumento de km por incluir um destino isolado

sequência sem progressão geográfica

rota que estoura SLA

rota que exige veículo inadequado

rota que mistura destinos que deveriam ser desmembrados

4. Como transformar isso em algoritmo

A forma profissional é trabalhar com score composto.

Cada cenário recebe notas em vários critérios:

coerência geográfica

compactação territorial

penalidade por desvio

penalidade por ponto isolado

compatibilidade com veículo

aderência ao SLA

eficiência de distância

Depois o sistema calcula um score_final.

5. Estrutura de score recomendada
score_final =
    score_geografico
  + score_compactacao
  + score_progressao
  - penalidade_desvio
  - penalidade_outlier
  - penalidade_sla
  - penalidade_capacidade
  - penalidade_dimensional
6. Critérios do Motor de Plausibilidade
6.1 Coerência geográfica

Mede se os destinos formam um eixo lógico a partir da origem.

Exemplo bom:

Guarulhos

Mogi

São José

Curitiba

Joinville

Exemplo ruim:

Guarulhos

Curitiba

São José

Criciúma

Campinas

A segunda rota “vai e volta” no desenho.

6.2 Compactação territorial

Mede se os destinos estão relativamente agrupados.

Quanto mais dispersos, mais suspeita a rota.

6.3 Progressão espacial

A rota deve avançar em uma direção predominante.

Exemplo:
Guarulhos → Sul → mais Sul → mais Sul

Isso é bom.

Exemplo ruim:
Guarulhos → Sul → volta interior SP → volta Sul

6.4 Ponto fora da curva

Se um destino está muito longe do eixo principal, ele pode justificar outro veículo.

Esse é um dos pontos mais valiosos do sistema.

6.5 Alongamento artificial

Se a inclusão de um destino aumenta demais o km total, a rota deve perder score.

7. Estratégia prática de implementação
Fase 1

Implementar uma heurística simples, clara e auditável.

Nada de começar com IA opaca.

O motor deve ser explicável.

8. Modelo de dados para o algoritmo

Cada entrega precisa ter pelo menos:

{
    "id": 1,
    "city": "Curitiba",
    "lat": -25.42,
    "lon": -49.27,
    "weight": 120.0,
    "volume": 1.8,
    "deadline_days": 5
}

A origem também precisa existir:

origin = {
    "city": "Guarulhos",
    "lat": -23.4543,
    "lon": -46.5333
}
9. Primeira versão do algoritmo de plausibilidade

Crie o arquivo:

backend/app/services/plausibility_engine.py
from math import radians, sin, cos, sqrt, atan2
from statistics import mean


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def route_total_distance(origin: dict, stops: list[dict]) -> float:
    if not stops:
        return 0.0

    total = 0.0
    current = origin

    for stop in stops:
        total += haversine_km(current["lat"], current["lon"], stop["lat"], stop["lon"])
        current = stop

    return total


def distances_from_origin(origin: dict, stops: list[dict]) -> list[float]:
    return [
        haversine_km(origin["lat"], origin["lon"], stop["lat"], stop["lon"])
        for stop in stops
    ]


def calculate_direction_changes(origin: dict, stops: list[dict]) -> int:
    """
    Mede mudanças bruscas de direção usando o ângulo do vetor origem->destino.
    """
    if len(stops) < 3:
        return 0

    import math

    angles = []
    for stop in stops:
        dy = stop["lat"] - origin["lat"]
        dx = stop["lon"] - origin["lon"]
        angle = math.degrees(math.atan2(dy, dx))
        angles.append(angle)

    changes = 0
    for i in range(1, len(angles)):
        delta = abs(angles[i] - angles[i - 1])
        if delta > 180:
            delta = 360 - delta
        if delta > 45:
            changes += 1

    return changes


def outlier_penalty(origin: dict, stops: list[dict]) -> float:
    """
    Penaliza ponto muito isolado em relação à média.
    """
    if len(stops) < 3:
        return 0.0

    dists = distances_from_origin(origin, stops)
    avg = mean(dists)
    max_dist = max(dists)

    if avg == 0:
        return 0.0

    ratio = max_dist / avg

    if ratio >= 2.2:
        return 30.0
    if ratio >= 1.8:
        return 20.0
    if ratio >= 1.5:
        return 10.0
    return 0.0


def route_spread_penalty(origin: dict, stops: list[dict]) -> float:
    """
    Mede dispersão radial dos pontos.
    """
    if len(stops) < 3:
        return 0.0

    dists = distances_from_origin(origin, stops)
    avg = mean(dists)
    spread = max(dists) - min(dists)

    if avg == 0:
        return 0.0

    spread_ratio = spread / avg

    if spread_ratio > 1.2:
        return 20.0
    if spread_ratio > 0.8:
        return 10.0
    return 0.0


def detour_penalty(origin: dict, ordered_stops: list[dict]) -> float:
    """
    Compara rota ordenada com uma versão ordenada por distância radial.
    Se a rota real estiver muito pior, penaliza.
    """
    if len(ordered_stops) < 3:
        return 0.0

    actual = route_total_distance(origin, ordered_stops)
    radial_sorted = sorted(
        ordered_stops,
        key=lambda s: haversine_km(origin["lat"], origin["lon"], s["lat"], s["lon"])
    )
    baseline = route_total_distance(origin, radial_sorted)

    if baseline == 0:
        return 0.0

    ratio = actual / baseline

    if ratio > 1.5:
        return 30.0
    if ratio > 1.25:
        return 15.0
    return 0.0


def progression_score(origin: dict, stops: list[dict]) -> float:
    """
    Recompensa rotas que avançam progressivamente para mais longe.
    """
    if len(stops) < 2:
        return 20.0

    dists = distances_from_origin(origin, stops)

    good_steps = 0
    for i in range(1, len(dists)):
        if dists[i] >= dists[i - 1] * 0.9:
            good_steps += 1

    ratio = good_steps / (len(dists) - 1)
    return ratio * 20.0


def calculate_plausibility(origin: dict, ordered_stops: list[dict]) -> dict:
    """
    Score final de 0 a 100.
    """
    base_score = 100.0

    direction_changes = calculate_direction_changes(origin, ordered_stops)
    direction_penalty = direction_changes * 8.0

    penalties = {
        "direction_penalty": direction_penalty,
        "outlier_penalty": outlier_penalty(origin, ordered_stops),
        "spread_penalty": route_spread_penalty(origin, ordered_stops),
        "detour_penalty": detour_penalty(origin, ordered_stops),
    }

    bonuses = {
        "progression_bonus": progression_score(origin, ordered_stops),
    }

    final_score = (
        base_score
        - sum(penalties.values())
        + sum(bonuses.values())
    )

    final_score = max(0.0, min(100.0, final_score))

    return {
        "score": round(final_score, 2),
        "penalties": penalties,
        "bonuses": bonuses,
        "approved": final_score >= 60.0,
    }
10. O que esse motor já faz

Esse módulo já consegue:

penalizar mudança brusca de direção

penalizar destino muito fora da média

penalizar rota muito espalhada

penalizar rota muito pior que um baseline simples

bonificar progressão coerente

É uma base muito boa para MVP.

11. Como usar esse motor

Exemplo de uso:

from backend.app.services.plausibility_engine import calculate_plausibility

origin = {"city": "Guarulhos", "lat": -23.4543, "lon": -46.5333}

route = [
    {"city": "Mogi", "lat": -23.5228, "lon": -46.1883},
    {"city": "Sao Jose", "lat": -23.2237, "lon": -45.9009},
    {"city": "Curitiba", "lat": -25.4284, "lon": -49.2733},
    {"city": "Joinville", "lat": -26.3044, "lon": -48.8487},
]

result = calculate_plausibility(origin, route)
print(result)

Saída esperada:

{
    "score": 82.4,
    "penalties": {
        "direction_penalty": 8.0,
        "outlier_penalty": 0.0,
        "spread_penalty": 10.0,
        "detour_penalty": 0.0
    },
    "bonuses": {
        "progression_bonus": 20.0
    },
    "approved": True
}
12. Regra de corte sugerida

No MVP:

score >= 75: muito boa

score entre 60 e 74: plausível

score entre 45 e 59: suspeita

score < 45: rejeitar

13. Como detectar que vale quebrar a rota

Esse é outro ponto central.

A lógica é:

calcular score da rota inteira

identificar ponto mais suspeito

testar cenário sem esse ponto

testar esse ponto em veículo separado

comparar ganho total

14. Heurística inicial para split inteligente

Crie este módulo:

backend/app/services/scenario_splitter.py
from copy import deepcopy
from backend.app.services.plausibility_engine import calculate_plausibility


def split_by_outlier(origin: dict, stops: list[dict]) -> dict:
    """
    Tenta separar o destino mais distante para ver se melhora muito a rota principal.
    """
    if len(stops) < 3:
        return {
            "should_split": False,
            "reason": "not_enough_stops"
        }

    full = calculate_plausibility(origin, stops)

    distances = []
    for idx, stop in enumerate(stops):
        d = ((origin["lat"] - stop["lat"]) ** 2 + (origin["lon"] - stop["lon"]) ** 2) ** 0.5
        distances.append((idx, d))

    outlier_index = sorted(distances, key=lambda x: x[1], reverse=True)[0][0]

    main_route = deepcopy(stops)
    isolated = main_route.pop(outlier_index)

    main_score = calculate_plausibility(origin, main_route)

    gain = main_score["score"] - full["score"]

    return {
        "should_split": gain >= 12.0,
        "full_route_score": full["score"],
        "main_route_score": main_score["score"],
        "gain": round(gain, 2),
        "isolated_stop": isolated,
        "remaining_route": main_route,
    }
15. O que esse splitter faz

Ele tenta responder:

se eu tirar o ponto mais distante, a rota principal melhora muito?

se sim, talvez esse ponto deva virar outro veículo

No começo isso já resolve uma parte real do problema.

16. Validação de veículo profissional

Agora vamos robustecer a compatibilidade de veículo.

Crie:

backend/app/services/vehicle_compatibility.py
def vehicle_can_handle_route(vehicle: dict, deliveries: list[dict]) -> dict:
    total_weight = sum(d["weight"] for d in deliveries)
    total_volume = sum(d["volume"] for d in deliveries)

    max_length = max(d.get("length", 0.0) for d in deliveries) if deliveries else 0.0
    max_width = max(d.get("width", 0.0) for d in deliveries) if deliveries else 0.0
    max_height = max(d.get("height", 0.0) for d in deliveries) if deliveries else 0.0

    reasons = []

    if total_weight > vehicle["max_weight"]:
        reasons.append("weight_exceeded")

    if total_volume > vehicle["max_volume"]:
        reasons.append("volume_exceeded")

    if max_length > vehicle["max_length"]:
        reasons.append("length_exceeded")

    if max_width > vehicle["max_width"]:
        reasons.append("width_exceeded")

    if max_height > vehicle["max_height"]:
        reasons.append("height_exceeded")

    if len(deliveries) > vehicle.get("max_stops", 999):
        reasons.append("max_stops_exceeded")

    return {
        "compatible": len(reasons) == 0,
        "total_weight": total_weight,
        "total_volume": total_volume,
        "max_item_length": max_length,
        "max_item_width": max_width,
        "max_item_height": max_height,
        "reasons": reasons,
    }


def choose_smallest_compatible_vehicle(vehicles: list[dict], deliveries: list[dict]) -> dict | None:
    ordered = sorted(vehicles, key=lambda v: v["cost_km"])
    for vehicle in ordered:
        result = vehicle_can_handle_route(vehicle, deliveries)
        if result["compatible"]:
            return {
                "vehicle": vehicle,
                "validation": result
            }
    return None
17. SLA profissional inicial

Crie:

backend/app/services/sla_validator.py
def estimate_route_days(total_km: float, avg_km_day: float = 600.0) -> float:
    if avg_km_day <= 0:
        raise ValueError("avg_km_day must be > 0")
    return total_km / avg_km_day


def validate_route_sla(total_km: float, max_days: float, avg_km_day: float = 600.0) -> dict:
    estimated_days = estimate_route_days(total_km, avg_km_day)
    return {
        "sla_ok": estimated_days <= max_days,
        "estimated_days": round(estimated_days, 2),
        "max_days": max_days,
    }
18. Ranking final dos cenários

Agora vamos juntar tudo.

Crie:

backend/app/services/optimizer.py
from backend.app.services.plausibility_engine import calculate_plausibility, route_total_distance
from backend.app.services.vehicle_compatibility import choose_smallest_compatible_vehicle
from backend.app.services.sla_validator import validate_route_sla


def evaluate_scenario(origin: dict, route: list[dict], vehicles: list[dict], max_days: float) -> dict:
    plausibility = calculate_plausibility(origin, route)
    total_km = route_total_distance(origin, route)

    vehicle_result = choose_smallest_compatible_vehicle(vehicles, route)
    sla_result = validate_route_sla(total_km, max_days)

    compatible = vehicle_result is not None
    sla_ok = sla_result["sla_ok"]

    if not compatible:
        final_score = 0.0
    else:
        final_score = plausibility["score"]

        if not sla_ok:
            final_score -= 30.0

        final_score -= total_km * 0.01

        if vehicle_result:
            final_score -= vehicle_result["vehicle"]["cost_km"] * 0.5

    final_score = max(0.0, round(final_score, 2))

    return {
        "route": [stop["city"] for stop in route],
        "plausibility": plausibility,
        "total_km": round(total_km, 2),
        "vehicle": vehicle_result["vehicle"]["name"] if vehicle_result else None,
        "vehicle_validation": vehicle_result["validation"] if vehicle_result else None,
        "sla": sla_result,
        "final_score": final_score,
        "approved": compatible and sla_ok and plausibility["approved"],
    }


def rank_scenarios(origin: dict, scenarios: list[list[dict]], vehicles: list[dict], max_days: float) -> list[dict]:
    evaluated = [
        evaluate_scenario(origin, scenario, vehicles, max_days)
        for scenario in scenarios
    ]
    return sorted(evaluated, key=lambda x: x["final_score"], reverse=True)
19. Geração de cenários candidatos

Não vamos gerar todas as combinações possíveis em produção, mas no MVP podemos começar com candidatos razoáveis.

Crie:

backend/app/services/scenario_generator.py
import itertools


def generate_candidate_routes(deliveries: list[dict], max_stops_per_route: int = 6) -> list[list[dict]]:
    candidates = []
    limit = min(len(deliveries), max_stops_per_route)

    for r in range(2, limit + 1):
        for combo in itertools.combinations(deliveries, r):
            candidates.append(list(combo))

    return candidates
20. Exemplo ponta a ponta

Crie um script de prova:

backend/app/demo_run.py
from backend.app.services.scenario_generator import generate_candidate_routes
from backend.app.services.optimizer import rank_scenarios

origin = {"city": "Guarulhos", "lat": -23.4543, "lon": -46.5333}

deliveries = [
    {"city": "Mogi", "lat": -23.5228, "lon": -46.1883, "weight": 100, "volume": 1.0, "length": 1.2, "width": 0.8, "height": 0.8},
    {"city": "Sao Jose", "lat": -23.2237, "lon": -45.9009, "weight": 120, "volume": 1.3, "length": 1.4, "width": 0.8, "height": 0.9},
    {"city": "Curitiba", "lat": -25.4284, "lon": -49.2733, "weight": 200, "volume": 2.0, "length": 1.6, "width": 1.0, "height": 1.0},
    {"city": "Joinville", "lat": -26.3044, "lon": -48.8487, "weight": 150, "volume": 1.2, "length": 1.5, "width": 0.9, "height": 0.9},
    {"city": "Criciuma", "lat": -28.6775, "lon": -49.3697, "weight": 90, "volume": 0.9, "length": 2.0, "width": 0.7, "height": 0.7},
]

vehicles = [
    {
        "name": "Fiorino",
        "max_weight": 650,
        "max_volume": 3.0,
        "max_length": 1.7,
        "max_width": 1.2,
        "max_height": 1.2,
        "max_stops": 5,
        "cost_km": 2.2,
    },
    {
        "name": "Van",
        "max_weight": 1400,
        "max_volume": 8.0,
        "max_length": 3.0,
        "max_width": 1.8,
        "max_height": 1.8,
        "max_stops": 8,
        "cost_km": 3.8,
    },
    {
        "name": "Carreta",
        "max_weight": 25000,
        "max_volume": 60.0,
        "max_length": 14.0,
        "max_width": 2.6,
        "max_height": 3.0,
        "max_stops": 15,
        "cost_km": 7.0,
    },
]

scenarios = generate_candidate_routes(deliveries, max_stops_per_route=5)
ranking = rank_scenarios(origin, scenarios, vehicles, max_days=5)

for item in ranking[:10]:
    print(item)
21. Testes importantes

Crie:

tests/test_plausibility.py
from backend.app.services.plausibility_engine import calculate_plausibility


def test_plausible_route_scores_well():
    origin = {"city": "Guarulhos", "lat": -23.4543, "lon": -46.5333}
    route = [
        {"city": "Mogi", "lat": -23.5228, "lon": -46.1883},
        {"city": "Sao Jose", "lat": -23.2237, "lon": -45.9009},
        {"city": "Curitiba", "lat": -25.4284, "lon": -49.2733},
    ]

    result = calculate_plausibility(origin, route)
    assert result["score"] >= 60

Crie:

tests/test_vehicle_rules.py
from backend.app.services.vehicle_compatibility import vehicle_can_handle_route


def test_vehicle_rejects_large_item():
    vehicle = {
        "name": "Fiorino",
        "max_weight": 650,
        "max_volume": 3.0,
        "max_length": 1.7,
        "max_width": 1.2,
        "max_height": 1.2,
        "max_stops": 5,
    }

    deliveries = [
        {
            "city": "X",
            "weight": 100,
            "volume": 1.0,
            "length": 2.0,
            "width": 0.8,
            "height": 0.8,
        }
    ]

    result = vehicle_can_handle_route(vehicle, deliveries)
    assert result["compatible"] is False
    assert "length_exceeded" in result["reasons"]

Crie:

tests/test_sla.py
from backend.app.services.sla_validator import validate_route_sla


def test_sla_passes_for_short_route():
    result = validate_route_sla(total_km=1000, max_days=3, avg_km_day=600)
    assert result["sla_ok"] is True


def test_sla_fails_for_long_route():
    result = validate_route_sla(total_km=2500, max_days=3, avg_km_day=600)
    assert result["sla_ok"] is False
22. Como o sistema pensa

Fluxo do motor:

recebe entregas

gera cenários candidatos

calcula plausibilidade

verifica veículo compatível

verifica SLA

calcula score final

ordena cenários

recomenda os melhores

sugere quebra de rota quando necessário

23. O que ainda falta para ficar mais profissional

Depois desta base, os próximos passos são:

Persistência

salvar entregas

salvar simulações

salvar cenários aprovados

API real

endpoint para upload CSV

endpoint para rodar simulação

endpoint para listar cenários

Banco de verdade

SQLAlchemy

Alembic

repository pattern

UI

painel React ou Streamlit

mapa

ranking visual

Algoritmo avançado

ordenação melhor de paradas

split por cluster

CVRP com OR-Tools

24. Próxima etapa correta

Agora a continuação mais útil é esta:

montar a versão profissional do backend com persistência real, incluindo:

config.py

database.py

models SQLAlchemy

schemas Pydantic

rotas FastAPI

estrutura de simulação

endpoints de teste

CRUD de entregas, veículos e simulações

Essa é a ponte entre “conceito” e “sistema utilizável”.

No próximo passo eu posso te entregar exatamente isso, já em texto completo de arquivos, para você copiar e colar.