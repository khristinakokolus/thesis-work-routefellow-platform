
CREATE TABLE trips (
    id UUID PRIMARY KEY,
    api_id TEXT,
    transport_type TEXT, -- whether it is a flight or a bus: for now such types as flight and bus
    type TEXT,
    availability INT,
    departure_point TEXT,
    arrival_point TEXT,
    price FLOAT,
    duration FLOAT,
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


CREATE TABLE flights (
    id UUID PRIMARY KEY,
    company_name TEXT,
    departure_point TEXT,
    arrival_point TEXT,
    trip_id UUID,
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


CREATE TABLE buses (
    id UUID PRIMARY KEY,
    company_name TEXT,
    departure_point TEXT,
    arrival_point TEXT,
    trip_id UUID,
    departure_time TIMESTAMP,
    arrival_time TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);


CREATE TABLE city_codes (
    id UUID PRIMARY KEY,
    city_name TEXT,
    city_code TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)