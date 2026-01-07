BEGIN;

ALTER TABLE store_memberships
  ADD COLUMN IF NOT EXISTS pay_rate_hourly numeric(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS tax_enabled boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS tax_rate_percent numeric(5,2) NOT NULL DEFAULT 0;

COMMIT;
