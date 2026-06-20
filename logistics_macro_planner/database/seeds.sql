-- Seed regions
INSERT INTO regions (name, lat, lon) VALUES ('Sul', -25.42, -49.27);
INSERT INTO regions (name, lat, lon) VALUES ('Sudeste', -23.55, -46.63);

-- Seed cities
INSERT INTO cities (name, region_id, lat, lon) VALUES ('Curitiba', 1, -25.4284, -49.2733);
INSERT INTO cities (name, region_id, lat, lon) VALUES ('Joinville', 1, -26.3045, -48.8456);
INSERT INTO cities (name, region_id, lat, lon) VALUES ('Florianopolis', 1, -27.5954, -48.5480);
INSERT INTO cities (name, region_id, lat, lon) VALUES ('Sao Paulo', 2, -23.5505, -46.6333);
INSERT INTO cities (name, region_id, lat, lon) VALUES ('Guarulhos', 2, -23.4543, -46.5333);

-- Seed vehicles
INSERT INTO vehicles (name, max_weight, max_volume, cost_km) VALUES ('Truck A', 10000, 50, 2.5);
INSERT INTO vehicles (name, max_weight, max_volume, cost_km) VALUES ('Van B', 1500, 10, 1.2);
INSERT INTO vehicles (name, max_weight, max_volume, cost_km) VALUES ('Motorcycle C', 50, 0.2, 0.5);
