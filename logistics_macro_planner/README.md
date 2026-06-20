# Logistics Macro Planner

Motor de planejamento logístico pré-TMS para otimização de cenários de transporte.

## Estrutura do Projeto

- `backend/app/`: Código fonte FastAPI.
  - `api/`: Endpoints REST.
  - `models/`: Modelos SQLAlchemy.
  - `services/`: Motores de roteirização (Plausibilidade, SLA, Otimização).
  - `utils/`: Cálculos geográficos.
- `database/`: Scripts SQL para schema e dados iniciais.
- `samples/`: Arquivos CSV de exemplo.
- `tests/`: Testes automatizados com `pytest`.

## Como Rodar

1. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Iniciar a API**:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

3. **Acessar documentação interativa**:
   Abra [http://localhost:8000/docs](http://localhost:8000/docs) para testar os endpoints.

## Endpoints Principais

- `GET /deliveries/`: Lista entregas.
- `POST /deliveries/`: Cria nova entrega.
- `GET /vehicles/`: Lista veículos.
- `POST /simulations/run`: Executa o motor de roteirização para encontrar o melhor cenário.

## Testes

Execute os testes com:
```bash
pytest
```
