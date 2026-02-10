-- AZALS - ROLLBACK Migration HR MODULE
-- Annule la creation du module ressources humaines (M3)

DO $$
BEGIN
    -- Drop triggers
    DROP TRIGGER IF EXISTS set_updated_at_hr_departments ON hr_departments;
    DROP TRIGGER IF EXISTS set_updated_at_hr_positions ON hr_positions;
    DROP TRIGGER IF EXISTS set_updated_at_hr_employees ON hr_employees;
    DROP TRIGGER IF EXISTS set_updated_at_hr_contracts ON hr_contracts;
    DROP TRIGGER IF EXISTS set_updated_at_hr_leave_requests ON hr_leave_requests;
    DROP TRIGGER IF EXISTS set_updated_at_hr_payroll_periods ON hr_payroll_periods;
    DROP TRIGGER IF EXISTS set_updated_at_hr_payslips ON hr_payslips;
    DROP TRIGGER IF EXISTS set_updated_at_hr_time_entries ON hr_time_entries;
    DROP TRIGGER IF EXISTS set_updated_at_hr_employee_skills ON hr_employee_skills;
    DROP TRIGGER IF EXISTS set_updated_at_hr_trainings ON hr_trainings;
    DROP TRIGGER IF EXISTS set_updated_at_hr_evaluations ON hr_evaluations;

    -- Drop indexes for hr_documents
    DROP INDEX IF EXISTS idx_hr_documents_tenant;
    DROP INDEX IF EXISTS idx_hr_documents_employee;
    DROP INDEX IF EXISTS idx_hr_documents_type;
    DROP INDEX IF EXISTS idx_hr_documents_expiry;

    -- Drop indexes for hr_evaluations
    DROP INDEX IF EXISTS idx_evaluations_tenant;
    DROP INDEX IF EXISTS idx_evaluations_employee;
    DROP INDEX IF EXISTS idx_evaluations_status;
    DROP INDEX IF EXISTS idx_evaluations_scheduled;

    -- Drop indexes for hr_training_participants
    DROP INDEX IF EXISTS idx_training_participants_tenant;
    DROP INDEX IF EXISTS idx_training_participants_training;
    DROP INDEX IF EXISTS idx_training_participants_employee;

    -- Drop indexes for hr_trainings
    DROP INDEX IF EXISTS idx_trainings_tenant;
    DROP INDEX IF EXISTS idx_trainings_dates;
    DROP INDEX IF EXISTS idx_trainings_status;

    -- Drop indexes for hr_employee_skills
    DROP INDEX IF EXISTS idx_employee_skills_tenant;
    DROP INDEX IF EXISTS idx_employee_skills_employee;

    -- Drop indexes for hr_skills
    DROP INDEX IF EXISTS idx_skills_tenant;
    DROP INDEX IF EXISTS idx_skills_category;

    -- Drop indexes for hr_time_entries
    DROP INDEX IF EXISTS idx_time_entries_tenant;
    DROP INDEX IF EXISTS idx_time_entries_employee;
    DROP INDEX IF EXISTS idx_time_entries_date;

    -- Drop indexes for hr_payslip_lines
    DROP INDEX IF EXISTS idx_payslip_lines_payslip;
    DROP INDEX IF EXISTS idx_payslip_lines_tenant;

    -- Drop indexes for hr_payslips
    DROP INDEX IF EXISTS idx_payslips_tenant;
    DROP INDEX IF EXISTS idx_payslips_employee;
    DROP INDEX IF EXISTS idx_payslips_period;
    DROP INDEX IF EXISTS idx_payslips_status;

    -- Drop indexes for hr_payroll_periods
    DROP INDEX IF EXISTS idx_payroll_periods_tenant;
    DROP INDEX IF EXISTS idx_payroll_periods_year;

    -- Drop indexes for hr_leave_balances
    DROP INDEX IF EXISTS idx_leave_balances_tenant;
    DROP INDEX IF EXISTS idx_leave_balances_employee;

    -- Drop indexes for hr_leave_requests
    DROP INDEX IF EXISTS idx_leaves_tenant;
    DROP INDEX IF EXISTS idx_leaves_employee;
    DROP INDEX IF EXISTS idx_leaves_status;
    DROP INDEX IF EXISTS idx_leaves_dates;

    -- Drop indexes for hr_contracts
    DROP INDEX IF EXISTS idx_contracts_tenant;
    DROP INDEX IF EXISTS idx_contracts_employee;
    DROP INDEX IF EXISTS idx_contracts_current;

    -- Drop indexes for hr_employees
    DROP INDEX IF EXISTS idx_employees_tenant;
    DROP INDEX IF EXISTS idx_employees_department;
    DROP INDEX IF EXISTS idx_employees_manager;
    DROP INDEX IF EXISTS idx_employees_status;
    DROP INDEX IF EXISTS idx_employees_hire_date;

    -- Drop indexes for hr_positions
    DROP INDEX IF EXISTS idx_positions_tenant;
    DROP INDEX IF EXISTS idx_positions_department;

    -- Drop indexes for hr_departments
    DROP INDEX IF EXISTS idx_departments_tenant;
    DROP INDEX IF EXISTS idx_departments_parent;

    -- Drop foreign key constraint before dropping tables
    ALTER TABLE IF EXISTS hr_departments DROP CONSTRAINT IF EXISTS fk_department_manager;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS hr_documents CASCADE;
    DROP TABLE IF EXISTS hr_evaluations CASCADE;
    DROP TABLE IF EXISTS hr_training_participants CASCADE;
    DROP TABLE IF EXISTS hr_trainings CASCADE;
    DROP TABLE IF EXISTS hr_employee_skills CASCADE;
    DROP TABLE IF EXISTS hr_skills CASCADE;
    DROP TABLE IF EXISTS hr_time_entries CASCADE;
    DROP TABLE IF EXISTS hr_payslip_lines CASCADE;
    DROP TABLE IF EXISTS hr_payslips CASCADE;
    DROP TABLE IF EXISTS hr_payroll_periods CASCADE;
    DROP TABLE IF EXISTS hr_leave_balances CASCADE;
    DROP TABLE IF EXISTS hr_leave_requests CASCADE;
    DROP TABLE IF EXISTS hr_contracts CASCADE;
    DROP TABLE IF EXISTS hr_employees CASCADE;
    DROP TABLE IF EXISTS hr_positions CASCADE;
    DROP TABLE IF EXISTS hr_departments CASCADE;

    -- Drop ENUM types
    DROP TYPE IF EXISTS training_status;
    DROP TYPE IF EXISTS training_type;
    DROP TYPE IF EXISTS evaluation_status;
    DROP TYPE IF EXISTS evaluation_type;
    DROP TYPE IF EXISTS hr_document_type;
    DROP TYPE IF EXISTS pay_element_type;
    DROP TYPE IF EXISTS payroll_status;
    DROP TYPE IF EXISTS leave_status;
    DROP TYPE IF EXISTS leave_type;
    DROP TYPE IF EXISTS employee_status;
    DROP TYPE IF EXISTS contract_type;

    RAISE NOTICE 'Migration 018_hr_module rolled back successfully';
END $$;
