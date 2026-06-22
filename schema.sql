CREATE TABLE IF NOT EXISTS app_settings (
    key VARCHAR(50) PRIMARY KEY,
    value VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS password_types (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT unique_user_type UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS password_subtypes (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    type_id INT REFERENCES password_types(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    CONSTRAINT unique_type_subtype UNIQUE (type_id, name)
);

CREATE TABLE IF NOT EXISTS passwords (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    type_id INT REFERENCES password_types(id) ON DELETE SET NULL,
    subtype_id INT REFERENCES password_subtypes(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    username_or_email VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL
);