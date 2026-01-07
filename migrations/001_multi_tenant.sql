BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- TENANTS
-- =========================================================
CREATE TABLE IF NOT EXISTS tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code varchar(64) UNIQUE NOT NULL,
  name varchar(128) NOT NULL,

  plan varchar(32) NOT NULL DEFAULT 'growth',
  billing_cycle varchar(16) NOT NULL DEFAULT 'monthly',
  max_stores integer NOT NULL DEFAULT 3,

  feature_payroll boolean NOT NULL DEFAULT true,
  feature_timeclock boolean NOT NULL DEFAULT true,
  feature_scheduling boolean NOT NULL DEFAULT true,
  feature_ai boolean NOT NULL DEFAULT false,

  is_active boolean NOT NULL DEFAULT true
);

-- Default tenant for existing legacy rows (safe)
INSERT INTO tenants (code, name)
VALUES ('default', 'Default Tenant')
ON CONFLICT (code) DO NOTHING;

-- =========================================================
-- USERS: tenant boundary (nullable because developer can have NULL)
-- =========================================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='users' AND column_name='tenant_id'
  ) THEN
    ALTER TABLE users ADD COLUMN tenant_id uuid NULL;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes WHERE indexname='ix_users_tenant_id'
  ) THEN
    CREATE INDEX ix_users_tenant_id ON users(tenant_id);
  END IF;
END $$;

-- =========================================================
-- STORES: tenant boundary (must be NOT NULL, but needs backfill first)
-- =========================================================
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='stores' AND column_name='tenant_id'
  ) THEN
    ALTER TABLE stores ADD COLUMN tenant_id uuid NULL;
  END IF;
END $$;

-- Backfill existing stores to default tenant
UPDATE stores
SET tenant_id = (SELECT id FROM tenants WHERE code='default')
WHERE tenant_id IS NULL;

-- Enforce NOT NULL now that data is filled
ALTER TABLE stores
  ALTER COLUMN tenant_id SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_stores_tenant_id ON stores(tenant_id);

-- Make store code unique per tenant (recommended for multi-tenant)
-- If you already have global unique constraint on stores(code), this removes it if it matches that name.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname='stores_code_key') THEN
    ALTER TABLE stores DROP CONSTRAINT stores_code_key;
  END IF;
EXCEPTION WHEN undefined_object THEN
  NULL;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_stores_tenant_code
ON stores(tenant_id, code);

COMMIT;
