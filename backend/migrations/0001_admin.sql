PRAGMA foreign_keys = ON;
CREATE TABLE owner (id INTEGER PRIMARY KEY CHECK (id = 1), username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, salt TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, expires_at INTEGER NOT NULL);
CREATE TABLE orders (id TEXT PRIMARY KEY, data TEXT NOT NULL CHECK(json_valid(data)), updated_at TEXT NOT NULL);
CREATE TABLE packages (id TEXT PRIMARY KEY, order_id TEXT NOT NULL REFERENCES orders(id), tracking_normalized TEXT UNIQUE, data TEXT NOT NULL CHECK(json_valid(data)), version INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL);
CREATE TABLE documents (id TEXT PRIMARY KEY, package_id TEXT NOT NULL REFERENCES packages(id), file_key TEXT NOT NULL UNIQUE, filename TEXT NOT NULL, kind TEXT NOT NULL, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE audit (id INTEGER PRIMARY KEY AUTOINCREMENT, actor TEXT NOT NULL, action TEXT NOT NULL, entity_id TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX audit_recent ON audit(created_at);
CREATE INDEX packages_order ON packages(order_id);
