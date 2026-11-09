CREATE TABLE tracking_items (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL CHECK(scope IN ('project','personal')),
  sort_order INTEGER NOT NULL DEFAULT 0,
  data TEXT NOT NULL CHECK(json_valid(data)),
  owner_marks TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(owner_marks)),
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);
CREATE INDEX tracking_items_scope ON tracking_items(scope,sort_order);
