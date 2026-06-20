// ============================================================
// Global State
// ============================================================
let map;
let markerLayerGroup;
let routePolyline;
let activeSimulationId = null;
let appState = {
    selectedDeliveries: [],
    selectedVehicles: [],
    currentView: 'main', // 'main' | 'results'
    lastConsolidation: null,
};

// ============================================================
// Initialize App
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadVehicles();
    loadDeliveries();
    loadHistory();
    setupEventListeners();
});

// ============================================================
// Map
// ============================================================
function initMap() {
    map = L.map('map').setView([-25.0, -48.0], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    markerLayerGroup = L.layerGroup().addTo(map);
}

// ============================================================
// Vehicles
// ============================================================
async function loadVehicles() {
    const container = document.getElementById('vehicle-checkboxes');
    try {
        const response = await fetch('/vehicles/?include_inactive=true');
        const vehicles = await response.json();

        container.innerHTML = '';
        if (vehicles.length === 0) {
            container.innerHTML = '<div class="checkbox-item loading">Nenhum veículo cadastrado. Crie um!</div>';
            return;
        }

        vehicles.forEach(vehicle => {
            const div = document.createElement('div');
            div.className = 'checkbox-item';
            const isInactive = vehicle.ativo === false;
            const inactiveLabel = isInactive ? ' <span style="color:var(--accent-red);font-size:10px">[INATIVO]</span>' : '';
            div.innerHTML = `
                <label style="display:flex;align-items:center;gap:8px;flex:1;cursor:pointer">
                    <input type="checkbox" name="vehicles" value="${vehicle.id}" ${isInactive ? '' : 'checked'} ${isInactive ? 'disabled' : ''}>
                    <span>${vehicle.name}${inactiveLabel}</span>
                    <span style="margin-left:auto;font-size:11px;color:var(--text-secondary)">
                        ${vehicle.max_weight}kg | ${vehicle.max_volume}m³ | R$${(vehicle.cost_km || 0).toFixed(2)}/km
                    </span>
                </label>
            `;
            container.appendChild(div);
        });
    } catch (err) {
        console.error('Error loading vehicles:', err);
        container.innerHTML = '<div class="checkbox-item error" style="color: var(--accent-red)">Erro ao carregar veículos</div>';
    }
}

// ============================================================
// Deliveries
// ============================================================
async function loadDeliveries() {
    const container = document.getElementById('delivery-checkboxes');
    try {
        const response = await fetch('/deliveries/');
        const deliveries = await response.json();

        container.innerHTML = '';
        if (deliveries.length === 0) {
            container.innerHTML = '<div class="checkbox-item loading">Nenhuma entrega cadastrada. Faça upload de um CSV!</div>';
            return;
        }

        deliveries.forEach(delivery => {
            const div = document.createElement('div');
            div.className = 'checkbox-item';
            div.dataset.deliveryId = delivery.id;

            const cityName = delivery.destino_cidade || `City ID: ${delivery.city_id}`;
            const origin = delivery.origem_cidade || '—';
            const volumeDisplay = delivery.volume_m3 ? delivery.volume_m3.toFixed(4) : '—';
            const prioridadeIcon = delivery.prioridade === 'alta' ? '🔴' : delivery.prioridade === 'media' ? '🟡' : '🟢';

            div.innerHTML = `
                <label style="display:flex;flex-direction:column;gap:2px;flex:1;cursor:pointer">
                    <div style="display:flex;align-items:center;gap:8px">
                        <input type="checkbox" name="deliveries" value="${delivery.id}" checked>
                        <strong>#${delivery.id} ${origin} → ${cityName}</strong>
                        <span class="compat-badge" id="compat-${delivery.id}"></span>
                    </div>
                    <div class="delivery-detail" style="padding-left:24px">
                        ${prioridadeIcon} ${delivery.peso_kg}kg | ${volumeDisplay}m³ | 
                        ${delivery.comprimento_cm}×${delivery.largura_cm}×${delivery.altura_cm}cm | 
                        ${delivery.deadline_days}d ${delivery.descricao ? '— ' + delivery.descricao : ''}
                    </div>
                </label>
            `;
            container.appendChild(div);
        });
    } catch (err) {
        console.error('Error loading deliveries:', err);
        container.innerHTML = '<div class="checkbox-item error" style="color: var(--accent-red)">Erro ao carregar entregas</div>';
    }
}

// ============================================================
// History
// ============================================================
async function loadHistory() {
    const container = document.getElementById('history-list');
    try {
        const response = await fetch('/simulations/');
        const history = await response.json();

        container.innerHTML = '';
        if (history.length === 0) {
            container.innerHTML = '<div class="checkbox-item loading">Nenhuma simulação realizada.</div>';
            return;
        }

        history.forEach(sim => {
            const div = document.createElement('div');
            div.className = 'history-item';
            if (sim.id === activeSimulationId) div.className += ' active';

            const bestRouteText = sim.best_route
                ? `${sim.best_route.vehicle} → ${sim.best_route.stops.join(', ')}`
                : 'Sem rotas viáveis';

            div.innerHTML = `
                <div class="info" onclick="loadSimulationDetail(${sim.id})">
                    <div class="title">Simulação #${sim.id} (${sim.origin})</div>
                    <div class="date">${bestRouteText}</div>
                </div>
                <div class="score">${sim.best_route ? sim.best_route.plausibility_score.toFixed(0) : 0}</div>
            `;
            container.appendChild(div);
        });
    } catch (err) {
        console.error('Error loading history:', err);
    }
}

// ============================================================
// Event Listeners
// ============================================================
function setupEventListeners() {
    // Select/Clear All
    document.getElementById('select-all-deliveries').addEventListener('click', () => {
        document.querySelectorAll('input[name="deliveries"]').forEach(cb => cb.checked = true);
    });

    document.getElementById('clear-all-deliveries').addEventListener('click', () => {
        document.querySelectorAll('input[name="deliveries"]').forEach(cb => cb.checked = false);
    });

    // CSV Upload
    document.getElementById('upload-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('csv-file');
        const statusMsg = document.getElementById('upload-status');
        const uploadBtn = document.getElementById('upload-btn');

        if (!fileInput.files || fileInput.files.length === 0) return;

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Importando...';
        statusMsg.className = 'status-msg';
        statusMsg.textContent = '';

        try {
            const response = await fetch('/deliveries/upload-csv', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (response.ok) {
                statusMsg.className = 'status-msg success';
                let msg = data.message;
                if (data.errors && data.errors.length > 0) {
                    msg += ` (${data.total_errors} erros)`;
                    console.warn('Import errors:', data.errors);
                }
                statusMsg.textContent = msg;
                loadDeliveries();
                fileInput.value = '';
            } else {
                statusMsg.className = 'status-msg error';
                statusMsg.textContent = data.detail || 'Falha no upload';
            }
        } catch (err) {
            statusMsg.className = 'status-msg error';
            statusMsg.textContent = 'Erro de conexão';
            console.error(err);
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload Entregas';
        }
    });

    // Run Simulation
    document.getElementById('sim-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const runBtn = document.getElementById('run-sim-btn');

        // Save state before navigation
        saveAppState();

        const origin_city_id = parseInt(document.getElementById('origin-select').value);
        const delivery_ids = Array.from(document.querySelectorAll('input[name="deliveries"]:checked'))
            .map(cb => parseInt(cb.value));
        const vehicle_ids = Array.from(document.querySelectorAll('input[name="vehicles"]:checked'))
            .map(cb => parseInt(cb.value));

        if (delivery_ids.length === 0) {
            alert('Selecione pelo menos uma entrega para roteirizar');
            return;
        }
        if (vehicle_ids.length === 0) {
            alert('Selecione pelo menos um veículo');
            return;
        }

        runBtn.disabled = true;
        runBtn.textContent = '⏳ Calculando cenários...';

        try {
            const response = await fetch('/simulations/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ origin_city_id, delivery_ids, vehicle_ids })
            });
            const data = await response.json();

            if (response.ok) {
                activeSimulationId = data.simulation_id;
                appState.lastConsolidation = data.consolidation;
                loadHistory();
                displayRunResults(data);
                showBackButton();
            } else {
                alert('Erro na simulação: ' + (data.detail || JSON.stringify(data)));
            }
        } catch (err) {
            alert('Erro de conexão ao executar simulação');
            console.error(err);
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = '⚡ Gerar & Otimizar Rotas';
        }
    });
}

// ============================================================
// State Management
// ============================================================
function saveAppState() {
    appState.selectedDeliveries = Array.from(document.querySelectorAll('input[name="deliveries"]:checked'))
        .map(cb => parseInt(cb.value));
    appState.selectedVehicles = Array.from(document.querySelectorAll('input[name="vehicles"]:checked'))
        .map(cb => parseInt(cb.value));
}

function restoreAppState() {
    // Restore delivery selections
    document.querySelectorAll('input[name="deliveries"]').forEach(cb => {
        cb.checked = appState.selectedDeliveries.includes(parseInt(cb.value));
    });
    // Restore vehicle selections
    document.querySelectorAll('input[name="vehicles"]').forEach(cb => {
        if (!cb.disabled) {
            cb.checked = appState.selectedVehicles.includes(parseInt(cb.value));
        }
    });
}

function showBackButton() {
    document.getElementById('btn-back').style.display = 'inline-flex';
    appState.currentView = 'results';
}

function goBack() {
    document.getElementById('btn-back').style.display = 'none';
    appState.currentView = 'main';
    restoreAppState();

    // Scroll sidebar to top
    document.getElementById('sidebar-section').scrollTop = 0;
}

// ============================================================
// Template Download
// ============================================================
function downloadTemplate() {
    window.location.href = '/deliveries/template-csv';
}

// ============================================================
// Delete All Deliveries
// ============================================================
async function deleteAllDeliveries() {
    if (!confirm('Tem certeza que deseja excluir TODAS as entregas cadastradas?')) return;

    try {
        const response = await fetch('/deliveries/', { method: 'DELETE' });
        const data = await response.json();
        if (response.ok) {
            loadDeliveries();
        }
    } catch (err) {
        alert('Erro ao excluir entregas');
        console.error(err);
    }
}

// ============================================================
// Vehicle Modal
// ============================================================
function openVehicleModal() {
    document.getElementById('vehicle-modal').style.display = 'flex';
}

function closeVehicleModal() {
    document.getElementById('vehicle-modal').style.display = 'none';
    document.getElementById('vehicle-form').reset();
}

async function submitVehicle(e) {
    e.preventDefault();
    const btn = document.getElementById('create-vehicle-btn');
    btn.disabled = true;
    btn.textContent = 'Criando...';

    const payload = {
        name: document.getElementById('v-name').value,
        tipo: document.getElementById('v-tipo').value,
        max_weight: parseFloat(document.getElementById('v-max-weight').value),
        max_volume: parseFloat(document.getElementById('v-max-volume').value),
        cost_km: parseFloat(document.getElementById('v-cost-km').value),
        max_length: parseFloat(document.getElementById('v-max-length').value) || 0,
        max_width: parseFloat(document.getElementById('v-max-width').value) || 0,
        max_height: parseFloat(document.getElementById('v-max-height').value) || 0,
    };

    try {
        const response = await fetch('/vehicles/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            closeVehicleModal();
            loadVehicles();
        } else {
            const data = await response.json();
            alert('Erro: ' + (data.detail || JSON.stringify(data)));
        }
    } catch (err) {
        alert('Erro de conexão');
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Criar Veículo';
    }
}

// ============================================================
// Display Run Results (from POST /simulations/run)
// ============================================================
function displayRunResults(data) {
    const bestCard = document.getElementById('best-route-card');
    const altsCard = document.getElementById('all-scenarios-card');

    // Clear map
    markerLayerGroup.clearLayers();
    if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
    }

    // Show consolidation results
    displayConsolidation(data.consolidation);

    // Show best scenario
    const best = data.best_scenario;
    if (!best || !best.vehicle) {
        bestCard.style.display = 'block';
        bestCard.querySelector('.card-header h2').textContent = 'Nenhum Cenário Viável';
        document.getElementById('best-score').textContent = '0';
        document.getElementById('best-vehicle').textContent = '—';
        document.getElementById('best-distance').textContent = '0 km';
        document.getElementById('best-plausibility').textContent = '0 / 100';
        document.getElementById('best-cost').textContent = 'R$ 0,00';
        document.getElementById('best-stops-flow').innerHTML = '<div class="stop-bubble origin">Sem paradas</div>';
        document.getElementById('split-warning').style.display = 'none';
        altsCard.style.display = 'none';
        return;
    }

    bestCard.style.display = 'block';
    document.getElementById('best-score').textContent = best.plausibility_score.toFixed(1);
    document.getElementById('best-vehicle').textContent = best.vehicle;
    document.getElementById('best-distance').textContent = `${best.total_distance.toFixed(1)} km`;
    document.getElementById('best-plausibility').textContent = `${best.plausibility_score.toFixed(1)} / 100`;
    document.getElementById('best-cost').textContent = formatCurrency(best.estimated_cost || 0);

    // Render stops
    const stopsFlow = document.getElementById('best-stops-flow');
    stopsFlow.innerHTML = `<div class="stop-bubble origin"><span class="type">🏭</span> Origem</div>`;
    best.stops.forEach((stop, index) => {
        stopsFlow.innerHTML += `<div class="stop-arrow">➔</div>`;
        stopsFlow.innerHTML += `<div class="stop-bubble"><span class="index">${index + 1}</span> ${stop}</div>`;
    });

    // Split recommendation
    const splitWarning = document.getElementById('split-warning');
    if (best.split_recommendation && best.split_recommendation.should_split) {
        splitWarning.style.display = 'flex';
        document.getElementById('split-message').textContent = best.split_recommendation.message;
    } else {
        splitWarning.style.display = 'none';
    }

    // Load full details for the map and alternatives table
    loadSimulationDetail(data.simulation_id);
}

// ============================================================
// Consolidation Display
// ============================================================
function displayConsolidation(consolidation) {
    const card = document.getElementById('consolidation-card');
    if (!consolidation || !consolidation.summary) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    const summary = consolidation.summary;

    // Total cost badge
    document.getElementById('total-cost-badge').textContent = formatCurrency(summary.total_cost || 0);

    // Summary stats
    const summaryDiv = document.getElementById('consolidation-summary');
    summaryDiv.innerHTML = `
        <div class="summary-stat">
            <div class="stat-value">${summary.total_deliveries}</div>
            <div class="stat-label">Total Entregas</div>
        </div>
        <div class="summary-stat">
            <div class="stat-value">${summary.allocated}</div>
            <div class="stat-label">Alocadas</div>
        </div>
        <div class="summary-stat">
            <div class="stat-value" style="color:${summary.unallocated > 0 ? 'var(--accent-red)' : 'var(--accent-green)'}">${summary.unallocated}</div>
            <div class="stat-label">Não Alocadas</div>
        </div>
        <div class="summary-stat">
            <div class="stat-value">${summary.vehicles_used}</div>
            <div class="stat-label">Veículos Usados</div>
        </div>
        <div class="summary-stat">
            <div class="stat-value">${summary.total_weight_kg.toFixed(1)} kg</div>
            <div class="stat-label">Peso Total</div>
        </div>
        <div class="summary-stat">
            <div class="stat-value">${summary.total_volume_m3.toFixed(4)} m³</div>
            <div class="stat-label">Volume Total</div>
        </div>
    `;

    // Alerts
    const alertsDiv = document.getElementById('consolidation-alerts');
    alertsDiv.innerHTML = '';
    if (consolidation.alerts && consolidation.alerts.length > 0) {
        consolidation.alerts.forEach(alert => {
            const level = alert.includes('🔴') || alert.includes('crítica') ? 'danger' :
                          alert.includes('🟡') || alert.includes('alta') ? 'warn' : 'info';
            alertsDiv.innerHTML += `<div class="alert-item ${level}">${alert}</div>`;
        });
    }

    // Vehicle allocations
    const allocDiv = document.getElementById('vehicle-allocations');
    allocDiv.innerHTML = '';
    if (consolidation.allocations) {
        consolidation.allocations.forEach(alloc => {
            const weightLevel = getBarLevel(alloc.occupation.weight_pct);
            const volumeLevel = getBarLevel(alloc.occupation.volume_pct);

            let deliveryChips = '';
            alloc.deliveries.forEach(d => {
                const label = d.descricao || d.destino_cidade || `#${d.id}`;
                deliveryChips += `
                    <div class="delivery-chip">
                        ${label} <span class="chip-weight">${d.peso_kg}kg</span>
                    </div>
                `;
            });

            allocDiv.innerHTML += `
                <div class="allocation-card">
                    <div class="allocation-header">
                        <div class="vehicle-info">
                            <span class="vehicle-icon">🚛</span>
                            <span class="vehicle-name">${alloc.vehicle_name}</span>
                            <span class="vehicle-tipo">${alloc.vehicle_tipo}</span>
                            <span style="font-size:11px;color:var(--text-secondary)">(${alloc.delivery_count} cargas)</span>
                        </div>
                        <span class="allocation-cost">${formatCurrency(alloc.estimated_cost)}</span>
                    </div>
                    <div class="occupation-bars">
                        <div class="occupation-bar">
                            <div class="bar-label">
                                <span>Peso</span>
                                <span>${alloc.occupation.weight_kg.toFixed(1)} / ${alloc.occupation.weight_max_kg} kg (${alloc.occupation.weight_pct}%)</span>
                            </div>
                            <div class="bar-track">
                                <div class="bar-fill level-${weightLevel}" style="width: ${Math.min(alloc.occupation.weight_pct, 100)}%"></div>
                            </div>
                        </div>
                        <div class="occupation-bar">
                            <div class="bar-label">
                                <span>Volume</span>
                                <span>${alloc.occupation.volume_m3.toFixed(4)} / ${alloc.occupation.volume_max_m3} m³ (${alloc.occupation.volume_pct}%)</span>
                            </div>
                            <div class="bar-track">
                                <div class="bar-fill level-${volumeLevel}" style="width: ${Math.min(alloc.occupation.volume_pct, 100)}%"></div>
                            </div>
                        </div>
                    </div>
                    <div class="allocation-deliveries">${deliveryChips}</div>
                </div>
            `;
        });
    }

    // Unallocated
    const unallocSection = document.getElementById('unallocated-section');
    if (consolidation.unallocated && consolidation.unallocated.length > 0) {
        unallocSection.style.display = 'block';
        const listDiv = document.getElementById('unallocated-list');
        listDiv.innerHTML = '';
        consolidation.unallocated.forEach(d => {
            listDiv.innerHTML += `
                <div class="delivery-chip" style="border-color: rgba(255,51,102,0.3)">
                    ${d.descricao || d.destino_cidade || '#' + d.id}
                    <span class="chip-weight" style="color:var(--accent-red)">${d.peso_kg}kg | ${d.volume_m3}m³</span>
                </div>
            `;
        });
    } else {
        unallocSection.style.display = 'none';
    }
}

function getBarLevel(pct) {
    if (pct > 95) return 'fail';
    if (pct > 80) return 'warn';
    return 'ok';
}

function formatCurrency(value) {
    return 'R$ ' + value.toFixed(2).replace('.', ',');
}

// ============================================================
// Fetch and Display Simulation Details by ID
// ============================================================
async function loadSimulationDetail(simulationId) {
    activeSimulationId = simulationId;

    // Highlight active in history
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.remove('active');
    });

    try {
        const response = await fetch(`/simulations/${simulationId}`);
        const sim = await response.json();
        displayResults(sim);
        showBackButton();
    } catch (err) {
        console.error('Error fetching simulation details:', err);
    }
}

// ============================================================
// Display results on screen and map (from GET /simulations/{id})
// ============================================================
function displayResults(sim) {
    const bestCard = document.getElementById('best-route-card');
    const altsCard = document.getElementById('all-scenarios-card');

    // Clear old map layers
    markerLayerGroup.clearLayers();
    if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
    }

    if (sim.routes.length === 0) {
        bestCard.style.display = 'block';
        bestCard.querySelector('.card-header h2').textContent = 'Nenhum Cenário Viável';
        document.getElementById('best-score').textContent = '0';
        document.getElementById('best-vehicle').textContent = '—';
        document.getElementById('best-distance').textContent = '0 km';
        document.getElementById('best-plausibility').textContent = '0 / 100';
        document.getElementById('best-cost').textContent = 'R$ 0,00';
        document.getElementById('best-stops-flow').innerHTML = '<div class="stop-bubble origin">Sem paradas</div>';
        document.getElementById('split-warning').style.display = 'none';
        altsCard.style.display = 'none';
        return;
    }

    // 1. Show Best Route Card
    bestCard.style.display = 'block';
    altsCard.style.display = 'block';

    const bestRoute = sim.routes.find(r => r.is_best) || sim.routes[0];

    document.getElementById('best-score').textContent = bestRoute.plausibility_score.toFixed(1);
    document.getElementById('best-vehicle').textContent = bestRoute.vehicle;
    document.getElementById('best-distance').textContent = `${bestRoute.total_distance.toFixed(1)} km`;
    document.getElementById('best-plausibility').textContent = `${bestRoute.plausibility_score.toFixed(1)} / 100`;
    document.getElementById('best-cost').textContent = formatCurrency(bestRoute.estimated_cost || 0);

    // Render stops
    const stopsFlow = document.getElementById('best-stops-flow');
    stopsFlow.innerHTML = `
        <div class="stop-bubble origin">
            <span class="type">🏭</span> ${sim.origin.city}
        </div>
    `;

    bestRoute.stops.forEach((stop, index) => {
        stopsFlow.innerHTML += `<div class="stop-arrow">➔</div>`;
        stopsFlow.innerHTML += `
            <div class="stop-bubble">
                <span class="index">${index + 1}</span> ${stop}
            </div>
        `;
    });

    // Split recommendation
    const splitWarning = document.getElementById('split-warning');
    if (sim.split_recommendation && sim.split_recommendation.should_split) {
        splitWarning.style.display = 'flex';
        document.getElementById('split-message').textContent = sim.split_recommendation.message;
    } else {
        splitWarning.style.display = 'none';
    }

    // 2. Render Alternatives Table
    const tbody = document.getElementById('scenarios-tbody');
    tbody.innerHTML = '';

    sim.routes.forEach((route, idx) => {
        const tr = document.createElement('tr');
        if (route.is_best) tr.className = 'best-row';

        tr.innerHTML = `
            <td class="rank-num">#${idx + 1} ${route.is_best ? '⭐' : ''}</td>
            <td><strong>${route.vehicle}</strong><br><span style="font-size:10px;color:var(--text-secondary)">${route.vehicle_tipo || ''}</span></td>
            <td>${route.stops.join(' ➔ ')}</td>
            <td>${route.total_distance.toFixed(1)} km</td>
            <td style="color:var(--accent-green);font-weight:700">${formatCurrency(route.estimated_cost || 0)}</td>
            <td class="tbl-score">${route.plausibility_score.toFixed(1)}</td>
            <td><button class="btn-sm" onclick="plotSpecificRoute(${JSON.stringify(sim.origin).replace(/"/g, '&quot;')}, ${JSON.stringify(route.stops_detailed).replace(/"/g, '&quot;')})">📍 Ver</button></td>
        `;
        tbody.appendChild(tr);
    });

    // 3. Plot Best Route on Map
    plotRouteOnMap(sim.origin, bestRoute.stops_detailed);
}

// ============================================================
// Map Plotting
// ============================================================
function plotRouteOnMap(origin, stops) {
    markerLayerGroup.clearLayers();
    if (routePolyline) {
        map.removeLayer(routePolyline);
        routePolyline = null;
    }

    if (!origin) return;

    // Add Origin Marker
    const originIcon = L.divIcon({
        className: 'origin-marker-icon',
        html: '<div style="background-color: var(--accent-blue); width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 15px rgba(0,210,255,0.5)"></div>',
        iconSize: [14, 14]
    });

    L.marker([origin.lat, origin.lon], { icon: originIcon })
        .addTo(markerLayerGroup)
        .bindPopup(`<strong>Origem: ${origin.city}</strong>`)
        .openPopup();

    const coordinates = [[origin.lat, origin.lon]];

    // Add Stops Markers
    if (stops && stops.length > 0) {
        stops.forEach((stop, index) => {
            const stopIcon = L.divIcon({
                className: 'stop-marker-icon',
                html: `<div style="background-color: var(--accent-purple); width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 12px rgba(157,78,221,0.5)"></div>`,
                iconSize: [12, 12]
            });

            L.marker([stop.lat, stop.lon], { icon: stopIcon })
                .addTo(markerLayerGroup)
                .bindPopup(`<strong>Parada ${index + 1}: ${stop.city}</strong>`);

            coordinates.push([stop.lat, stop.lon]);
        });
    }

    // Draw Polyline
    routePolyline = L.polyline(coordinates, {
        color: '#00d2ff',
        weight: 3,
        opacity: 0.8,
        dashArray: '5, 10'
    }).addTo(map);

    // Zoom to fit
    const bounds = L.latLngBounds(coordinates);
    map.fitBounds(bounds, { padding: [50, 50] });
}

// Global scope binder
window.plotSpecificRoute = function(origin, stops) {
    plotRouteOnMap(origin, stops);
};
