CREATE TABLE tracking_items_next (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL CHECK(scope IN ('project','personal','unassigned')),
  sort_order INTEGER NOT NULL DEFAULT 0,
  data TEXT NOT NULL CHECK(json_valid(data)),
  owner_marks TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(owner_marks)),
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);
INSERT INTO tracking_items_next (id,scope,sort_order,data,owner_marks,version,updated_at)
SELECT id,scope,sort_order,data,owner_marks,version,updated_at FROM tracking_items;
DROP TABLE tracking_items;
ALTER TABLE tracking_items_next RENAME TO tracking_items;
CREATE INDEX tracking_items_scope ON tracking_items(scope,sort_order);
