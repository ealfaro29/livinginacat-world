ALTER TABLE sessions ADD COLUMN scope TEXT NOT NULL DEFAULT 'operator' CHECK (scope IN ('operator', 'phone'));
