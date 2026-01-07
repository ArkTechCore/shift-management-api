BEGIN;

-- Needs pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1) Add payroll fields to store_memberships (store-specific employee settings)
ALTER TABLE store_memberships
  ADD COLUMN IF NOT EXISTS pay_rate_hourly NUMERIC(10,2) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS tax_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS tax_rate_percent NUMERIC(5,2) NOT NULL DEFAULT 0;

-- 2) Payroll invoices table
CREATE TABLE IF NOT EXISTS payroll_invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  tenant_id UUID NOT NULL,
  store_id UUID NOT NULL,
  employee_id UUID NOT NULL,

  week_start DATE NOT NULL,                  -- same "week_start" you already use in existing payroll summary routes

  invoice_no BIGSERIAL NOT NULL,             -- NOT random, sequential, easy for UI

  pay_rate_hourly NUMERIC(10,2) NOT NULL DEFAULT 0,

  regular_minutes INTEGER NOT NULL DEFAULT 0,
  overtime_minutes INTEGER NOT NULL DEFAULT 0,

  gross_pay NUMERIC(12,2) NOT NULL DEFAULT 0,

  tax_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  tax_rate_percent NUMERIC(5,2) NOT NULL DEFAULT 0,
  tax_withheld NUMERIC(12,2) NOT NULL DEFAULT 0,

  net_pay NUMERIC(12,2) NOT NULL DEFAULT 0,

  status VARCHAR(24) NOT NULL DEFAULT 'issued',  -- issued|voided (no deletes, only status change later if needed)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Uniqueness: one invoice per employee per store per week
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_invoice_store_week_employee'
  ) THEN
    ALTER TABLE payroll_invoices
      ADD CONSTRAINT uq_invoice_store_week_employee UNIQUE (store_id, employee_id, week_start);
  END IF;
END $$;

-- Helpful indexes
CREATE INDEX IF NOT EXISTS ix_payroll_invoices_tenant ON payroll_invoices(tenant_id);
CREATE INDEX IF NOT EXISTS ix_payroll_invoices_store_week ON payroll_invoices(store_id, week_start);
CREATE INDEX IF NOT EXISTS ix_payroll_invoices_employee_week ON payroll_invoices(employee_id, week_start);

COMMIT;
