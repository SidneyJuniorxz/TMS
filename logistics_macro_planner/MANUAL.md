# Manual do Sistema — Logistics Macro Planner v2

## Visão Geral

O **Logistics Macro Planner** é um motor de planejamento logístico pré-TMS (Transportation Management System) que simula a consolidação inteligente de entregas em veículos, otimizando rotas por custo, distância e plausibilidade.

**Backend:** FastAPI + SQLite  
**Frontend:** HTML/CSS/JS + Leaflet.js (mapa interativo)

---

## 1. Como Rodar

### Backend (API)
```bash
cd /caminho/do/projeto/logistics_macro_planner
python3 run.py
```
O servidor inicia em `http://127.0.0.1:8000`.

### Em Produção (PM2)
```bash
pm2 restart tms-api
pm2 logs tms-api --lines 20
```

### Frontend
O frontend é servido automaticamente pelo FastAPI como arquivos estáticos em `backend/app/static/`. Acesse `http://127.0.0.1:8000` no navegador.

### Variáveis de Ambiente
| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./logistics.db` | URL de conexão do banco de dados |

### Porta Utilizada
| Serviço | Porta | Verificação |
|---|---|---|
| tms-api | 8000 | `lsof -i :8000` ou `ss -tlnp | grep 8000` |

> ⚠️ **Importante:** Antes de iniciar o serviço, sempre verifique se a porta 8000 está livre:
> ```bash
> ss -tlnp | grep 8000
> ```

---

## 2. Formato do CSV de Importação

### Colunas Obrigatórias
| Coluna | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `origem_cidade` | Texto | ✅ | Cidade de origem da entrega |
| `origem_cep` | Texto | ✅ | CEP de origem (formato: XXXXX-XXX) |
| `destino_cidade` | Texto | ✅ | Cidade de destino da entrega |
| `destino_cep` | Texto | ✅ | CEP de destino (formato: XXXXX-XXX) |
| `peso_kg` | Número | ✅ | Peso da carga em quilogramas (> 0) |
| `comprimento_cm` | Número | ✅ | Comprimento da carga em centímetros (> 0) |
| `largura_cm` | Número | ✅ | Largura da carga em centímetros (> 0) |
| `altura_cm` | Número | ✅ | Altura da carga em centímetros (> 0) |
| `deadline` | Número | Opcional | Prazo de entrega em dias (padrão: 5) |
| `descricao` | Texto | Opcional | Descrição da carga |
| `prioridade` | Texto | Opcional | `alta`, `media` ou `baixa` (padrão: media) |
| `observacao` | Texto | Opcional | Observações adicionais |

### Exemplo de CSV
```csv
origem_cidade,origem_cep,destino_cidade,destino_cep,peso_kg,comprimento_cm,largura_cm,altura_cm,deadline,descricao,prioridade,observacao
Guarulhos,07000-000,Osasco,06000-000,150,80,60,50,3,Peças automotivas,alta,Frágil
Guarulhos,07000-000,Santo André,09000-000,300,120,80,60,5,Eletrodomésticos,media,
Guarulhos,07000-000,São Bernardo do Campo,09600-000,80,50,40,30,2,Componentes eletrônicos,alta,Urgente
Guarulhos,07000-000,Barueri,06400-000,500,150,100,80,7,Materiais de construção,baixa,
Guarulhos,07000-000,São Paulo,01000-000,200,100,70,50,4,Alimentos secos,media,Manter seco
```

> 💡 **Dica:** Use o botão "Baixar Modelo de Importação" na interface para obter um arquivo CSV pronto com dados de exemplo.

### Validações na Importação
- CEPs de origem e destino são **obrigatórios**
- Peso deve ser **maior que zero**
- As 3 dimensões (comprimento, largura, altura) devem ser **maiores que zero**
- O volume (m³) é **calculado automaticamente** — não precisa ser informado

---

## 3. Regra de Cubagem (Cálculo de Volume)

```
volume_m3 = comprimento_cm × largura_cm × altura_cm / 1.000.000
```

**Exemplos:**
| Comprimento | Largura | Altura | Volume (m³) |
|---|---|---|---|
| 100 cm | 60 cm | 50 cm | 0,30 m³ |
| 80 cm | 60 cm | 50 cm | 0,24 m³ |
| 200 cm | 150 cm | 100 cm | 3,00 m³ |

---

## 4. Cadastro de Veículos

### Campos do Veículo
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `nome` | Texto | ✅ | Nome identificador do veículo |
| `tipo` | Texto | ✅ | Tipo (Van, Truck, Carreta, Furgão, VUC, Bitrem) |
| `peso_max_kg` | Número | ✅ | Peso máximo suportado em kg |
| `volume_max_m3` | Número | ✅ | Volume máximo em m³ |
| `comprimento_max_m` | Número | Opcional | Comprimento interno em metros |
| `largura_max_m` | Número | Opcional | Largura interna em metros |
| `altura_max_m` | Número | Opcional | Altura interna em metros |
| `custo_km` | Número | ✅ | Custo por quilômetro em R$ |

### Como Cadastrar
1. Na interface, clique no botão **"+ Criar Veículo"** ao lado de "Veículos Disponíveis"
2. Preencha o formulário no modal
3. Clique em **"Criar Veículo"**

---

## 5. Regra de Compatibilidade Veículo ↔ Carga

Uma carga é **compatível** com um veículo se:

1. `peso_kg` ≤ `veículo.peso_max_kg`
2. `volume_m3` ≤ `veículo.volume_max_m3`
3. `comprimento_cm` ≤ `veículo.comprimento_max_m × 100`
4. `largura_cm` ≤ `veículo.largura_max_m × 100`
5. `altura_cm` ≤ `veículo.altura_max_m × 100`

### Indicadores Visuais
| Indicador | Significado |
|---|---|
| 🟢 Verde | Compatível — ocupação < 80% |
| 🟡 Amarelo | Atenção — ocupação entre 80% e 100% |
| 🔴 Vermelho | Incompatível — excede capacidade |

---

## 6. Motor de Consolidação Inteligente

O sistema utiliza o algoritmo **First Fit Decreasing (FFD)** para alocar cargas em veículos:

### Algoritmo
1. Ordena entregas por **volume decrescente**
2. Para cada entrega:
   - Tenta alocar no primeiro veículo com capacidade residual suficiente
   - Se nenhum veículo existente cabe, abre um **novo veículo** (preferindo os mais baratos)
3. Respeita restrições de: peso, volume e dimensões (comprimento, largura, altura)
4. Cargas que não cabem em nenhum veículo vão para a lista de **"Não Alocadas"**

### Cálculo de Custo
```
custo_por_veículo = distância_km × custo_km_do_veículo
custo_total = soma(custo_por_veículo)
```

### Barras de Ocupação
Cada veículo exibe barras de ocupação para peso e volume:
- **Verde:** < 80%
- **Amarelo:** 80–95%
- **Vermelho:** > 95%

---

## 7. Otimização de Rotas (Plausibilidade)

O motor avalia cenários de rota com base em:

1. **Score Base:** 100 pontos
2. **Bônus de Progressão:** Rotas que avançam progressivamente (até +30)
3. **Penalidade de Outlier:** Destinos muito distantes da média (-10 a -30)
4. **Penalidade de Dispersão:** Destinos muito espalhados (-10 a -20)
5. **Penalidade de Desvio:** Rota real vs rota ótima por distância radial (-15 a -30)
6. **Mudanças de Direção:** -5 pontos por mudança > 45° entre destinos consecutivos

### Recomendação de Split
Se separar o destino mais isolado melhorar o score em ≥ 12 pontos, o sistema sugere dividir a rota.

---

## 8. Endpoints da API REST

### Entregas
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/deliveries/` | Lista todas as entregas |
| `POST` | `/deliveries/` | Cria uma entrega individual |
| `POST` | `/deliveries/upload-csv` | Importa entregas via CSV |
| `GET` | `/deliveries/template-csv` | Baixa modelo CSV com exemplos |
| `DELETE` | `/deliveries/{id}` | Remove uma entrega |
| `DELETE` | `/deliveries/` | Remove todas as entregas |

### Veículos
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/vehicles/` | Lista veículos (ativos por padrão) |
| `POST` | `/vehicles/` | Cria um veículo |
| `PUT` | `/vehicles/{id}` | Atualiza um veículo |
| `DELETE` | `/vehicles/{id}` | Remove um veículo |
| `PATCH` | `/vehicles/{id}/toggle` | Ativa/desativa veículo |

### Simulações
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/simulations/run` | Executa uma simulação |
| `GET` | `/simulations/` | Lista histórico de simulações |
| `GET` | `/simulations/{id}` | Detalhes de uma simulação |
| `DELETE` | `/simulations/{id}` | Remove uma simulação |

---

## 9. Deploy via PM2 e Cloudflare Tunnel

### Serviços PM2
| Nome | Script | Tipo |
|---|---|---|
| `tms-api` | `run.py` | Backend FastAPI (porta 8000) |
| `tms-tunnel` | `cloudflared tunnel` | Túnel Cloudflare |

### Comandos PM2 Úteis
```bash
# Status
pm2 list | grep tms

# Reiniciar API
pm2 restart tms-api

# Logs em tempo real
pm2 logs tms-api

# Salvar configuração (persiste no reboot)
pm2 save
```

### Cloudflare Tunnel
O túnel mapeia o domínio para o serviço local na porta 8000.

---

## 10. Migração de Banco de Dados

Ao atualizar para a v2, execute a migração uma vez:
```bash
cd /caminho/do/projeto/logistics_macro_planner
python3 scripts/migrate_v2.py
```

A migração é **aditiva** (não destrói dados existentes):
- Adiciona novas colunas às tabelas `deliveries` e `vehicles`
- Converte dados legados (`weight` → `peso_kg`, `volume` → `volume_m3`)
- Resolve nomes de cidade a partir de `city_id`

---

## 11. Estrutura do Projeto

```
logistics_macro_planner/
├── backend/app/
│   ├── api/
│   │   ├── deliveries.py    # CRUD + CSV + Template
│   │   ├── vehicles.py      # CRUD + Toggle
│   │   └── simulations.py   # Simulação + Consolidação
│   ├── models/
│   │   ├── delivery.py      # Modelo v2 (CEP, dimensões)
│   │   ├── vehicle.py       # Modelo v2 (tipo, ativo)
│   │   ├── simulation.py    # Simulação + Rotas
│   │   ├── city.py           # Cidades pré-cadastradas
│   │   └── region.py         # Regiões logísticas
│   ├── services/
│   │   ├── consolidation_engine.py  # Bin Packing FFD
│   │   ├── scenario_generator.py    # Clustering + Combinatória
│   │   ├── plausibility_engine.py   # Score de plausibilidade
│   │   ├── vehicle_compatibility.py # Checagem dimensional
│   │   ├── sla_validator.py         # Validação de SLA
│   │   ├── scenario_splitter.py     # Sugestão de split
│   │   └── optimizer.py             # Seleção do melhor cenário
│   ├── utils/geo_utils.py   # Haversine + distância total
│   ├── static/
│   │   ├── index.html        # Dashboard
│   │   ├── style.css          # Glassmorphism Dark Mode
│   │   └── app.js             # Leaflet + interação
│   ├── database.py            # SQLAlchemy config
│   └── main.py                # FastAPI app
├── database/schema.sql        # Schema SQL v2
├── scripts/migrate_v2.py      # Migração v1 → v2
├── samples/deliveries.csv     # CSV de exemplo v2
├── tests/test_engine.py       # 16 testes automatizados
├── run.py                     # Entry point PM2
├── logistics.db               # Banco SQLite
└── requirements.txt           # Dependências Python
```
