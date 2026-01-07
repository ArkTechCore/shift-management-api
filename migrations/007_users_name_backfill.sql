BEGIN;

UPDATE users
SET name = full_name
WHERE name IS NULL
  AND full_name IS NOT NULL;

COMMIT;
