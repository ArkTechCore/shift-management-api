BEGIN;

-- Add tenant boundary if missing
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS tenant_id uuid NULL;

-- Profile fields
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS name varchar(120) NULL,
  ADD COLUMN IF NOT EXISTS phone varchar(32) NULL;

-- Account status / lifecycle
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS status varchar(24) NOT NULL DEFAULT 'active';

-- Password reset / security fields
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS must_change_password boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS temp_password_issued_at timestamptz NULL,
  ADD COLUMN IF NOT EXISTS password_changed_at timestamptz NULL,
  ADD COLUMN IF NOT EXISTS failed_login_count integer NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS locked_until timestamptz NULL;

-- created_at (if missing)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();

-- indexes
CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users(tenant_id);

COMMIT;
