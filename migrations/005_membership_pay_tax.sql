BEGIN;

-- Add new columns (safe if already exist)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='store_memberships' AND column_name='pay_rate_hourly'
  ) THEN
    ALTER TABLE store_memberships ADD COLUMN pay_rate_hourly numeric(10,2) NOT NULL DEFAULT 0;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='store_memberships' AND column_name='tax_enabled'
  ) THEN
    ALTER TABLE store_memberships ADD COLUMN tax_enabled boolean NOT NULL DEFAULT false;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='store_memberships' AND column_name='tax_rate_percent'
  ) THEN
    ALTER TABLE store_memberships ADD COLUMN tax_rate_percent numeric(5,2) NOT NULL DEFAULT 0;
  END IF;
END $$;

-- Migrate old string pay_rate -> new numeric pay_rate_hourly (if old column exists)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='store_memberships' AND column_name='pay_rate'
  ) THEN
    UPDATE store_memberships
    SET pay_rate_hourly = COALESCE(NULLIF(regexp_replace(pay_rate, '[^0-9\.]', '', 'g'), ''), '0')::numeric(10,2)
    WHERE pay_rate_hourly = 0;

    ALTER TABLE store_memberships DROP COLUMN pay_rate;
  END IF;
END $$;

-- Helpful uniqueness (prevents duplicates)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_store_memberships_user_store') THEN
    ALTER TABLE store_memberships
      ADD CONSTRAINT uq_store_memberships_user_store UNIQUE (user_id, store_id);
  END IF;
END $$;

COMMIT;
