CREATE TABLE IF NOT EXISTS phone_pairing (
    token_hash TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    expires INTEGER NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0 CHECK (approved IN (0,1))
);
CREATE INDEX IF NOT EXISTS phone_pairing_expiration ON phone_pairing(expires);
