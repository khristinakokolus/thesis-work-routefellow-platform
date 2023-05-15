
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username TEXT,
    email TEXT,
    password TEXT,
    log_in BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
