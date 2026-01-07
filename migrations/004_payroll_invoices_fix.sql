BEGIN;

-- payroll_invoices table (create if missing)
CREATE TABLE IF NOT EXISTS payroll_invoices (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  tenant_id uuid NOT NULL,
  store_id uuid NOT NULL,
  employee_id uuid NOT NULL,

  week_start date NOT NULL,

  invoice_no bigint NOT NULL,

  pay_rate_hourly numeric(10,2) NOT NULL DEFAULT 0,

  regular_minutes integer NOT NULL DEFAULT 0,
  overtime_minutes integer NOT NULL DEFAULT 0,

  gross_pay numeric(12,2) NOT NULL DEFAULT 0,

  tax_enabled boolean NOT NULL DEFAULT false,
  tax_rate_percent numeric(5,2) NOT NULL DEFAULT 0,
  tax_withheld numeric(12,2) NOT NULL DEFAULT 0,

  net_pay numeric(12,2) NOT NULL DEFAULT 0,

  status varchar(24) NOT NULL DEFAULT 'issued',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- indexes
CREATE INDEX IF NOT EXISTS ix_payroll_invoices_tenant_id ON payroll_invoices(tenant_id);
CREATE INDEX IF NOT EXISTS ix_payroll_invoices_store_week ON payroll_invoices(store_id, week_start);
CREATE INDEX IF NOT EXISTS ix_payroll_invoices_employee_week ON payroll_invoices(employee_id, week_start);
CREATE INDEX IF NOT EXISTS ix_payroll_invoices_invoice_no ON payroll_invoices(invoice_no);

-- immutability rule via uniqueness (prevents duplicates)
-- one invoice per employee per store per week
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_invoice_store_emp_week'
  ) THEN
    ALTER TABLE payroll_invoices
      ADD CONSTRAINT uq_invoice_store_emp_week UNIQUE (store_id, employee_id, week_start);
  END IF;
END $$;

COMMIT;
