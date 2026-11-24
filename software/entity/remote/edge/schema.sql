CREATE TABLE IF NOT EXISTS operator (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    username TEXT NOT NULL UNIQUE,
    salt TEXT NOT NULL,
    verifier TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    expires INTEGER NOT NULL,
    scope TEXT NOT NULL DEFAULT 'operator' CHECK (scope IN ('operator', 'phone'))
);
CREATE INDEX IF NOT EXISTS sessions_expiration ON sessions(expires);
CREATE TABLE IF NOT EXISTS phone_pairing (
    token_hash TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    expires INTEGER NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0 CHECK (approved IN (0,1))
);
CREATE INDEX IF NOT EXISTS phone_pairing_expiration ON phone_pairing(expires);
