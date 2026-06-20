CREATE TABLE regions(
 id SERIAL PRIMARY KEY,
 name TEXT,
 lat FLOAT,
 lon FLOAT
);

CREATE TABLE cities(
 id SERIAL PRIMARY KEY,
 name TEXT,
 region_id INT REFERENCES regions(id),
 lat FLOAT,
 lon FLOAT
);

CREATE TABLE vehicles(
 id SERIAL PRIMARY KEY,
 name TEXT,
 tipo TEXT DEFAULT 'Truck',
 max_weight FLOAT,
 max_volume FLOAT,
 max_length FLOAT,
 max_width FLOAT,
 max_height FLOAT,
 cost_km FLOAT,
 ativo BOOLEAN DEFAULT TRUE
);

CREATE TABLE deliveries(
 id SERIAL PRIMARY KEY,
 city_id INT REFERENCES cities(id),
 origem_cidade TEXT DEFAULT '',
 origem_cep TEXT DEFAULT '',
 destino_cidade TEXT DEFAULT '',
 destino_cep TEXT DEFAULT '',
 peso_kg FLOAT DEFAULT 0,
 comprimento_cm FLOAT DEFAULT 0,
 largura_cm FLOAT DEFAULT 0,
 altura_cm FLOAT DEFAULT 0,
 volume_m3 FLOAT DEFAULT 0,
 deadline_days INT DEFAULT 5,
 descricao TEXT DEFAULT '',
 prioridade TEXT DEFAULT 'media',
 observacao TEXT DEFAULT '',
 weight FLOAT,
 volume FLOAT
);

CREATE TABLE simulations(
 id SERIAL PRIMARY KEY,
 origin_city_id INT REFERENCES cities(id),
 created_at TEXT DEFAULT CURRENT_TIMESTAMP,
 status TEXT
);

CREATE TABLE routes(
 id SERIAL PRIMARY KEY,
 simulation_id INT REFERENCES simulations(id) ON DELETE CASCADE,
 vehicle_id INT REFERENCES vehicles(id),
 total_distance FLOAT,
 plausibility_score FLOAT,
 final_score FLOAT,
 estimated_cost FLOAT DEFAULT 0,
 approved BOOLEAN,
 is_best BOOLEAN
);

CREATE TABLE route_stops(
 id SERIAL PRIMARY KEY,
 route_id INT REFERENCES routes(id) ON DELETE CASCADE,
 city_id INT REFERENCES cities(id),
 stop_order INT
);

CREATE TABLE simulation_deliveries(
 simulation_id INT REFERENCES simulations(id) ON DELETE CASCADE,
 delivery_id INT REFERENCES deliveries(id) ON DELETE CASCADE,
 PRIMARY KEY (simulation_id, delivery_id)
);

CREATE TABLE simulation_vehicles(
 simulation_id INT REFERENCES simulations(id) ON DELETE CASCADE,
 vehicle_id INT REFERENCES vehicles(id) ON DELETE CASCADE,
 PRIMARY KEY (simulation_id, vehicle_id)
);
