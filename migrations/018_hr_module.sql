-- ============================================================================
-- AZALS MODULE M3 - RH (Ressources Humaines)
-- Migration: 018_hr_module.sql
-- ============================================================================

-- Types enum pour le module RH
CREATE TYPE contract_type AS ENUM ('CDI', 'CDD', 'INTERIM', 'STAGE', 'APPRENTISSAGE', 'FREELANCE');
CREATE TYPE employee_status AS ENUM ('ACTIVE', 'ON_LEAVE', 'SUSPENDED', 'TERMINATED', 'RETIRED');
CREATE TYPE leave_type AS ENUM ('PAID', 'UNPAID', 'SICK', 'MATERNITY', 'PATERNITY', 'PARENTAL', 'RTT', 'TRAINING', 'SPECIAL', 'COMPENSATION');
CREATE TYPE leave_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED');
CREATE TYPE payroll_status AS ENUM ('DRAFT', 'CALCULATED', 'VALIDATED', 'PAID', 'CANCELLED');
CREATE TYPE pay_element_type AS ENUM ('GROSS_SALARY', 'BONUS', 'COMMISSION', 'OVERTIME', 'ALLOWANCE', 'DEDUCTION', 'SOCIAL_CHARGE', 'EMPLOYER_CHARGE', 'TAX', 'ADVANCE', 'REIMBURSEMENT');
CREATE TYPE hr_document_type AS ENUM ('CONTRACT', 'AMENDMENT', 'PAYSLIP', 'CERTIFICATE', 'WARNING', 'EVALUATION', 'TRAINING_CERT', 'ID_DOCUMENT', 'OTHER');
CREATE TYPE evaluation_type AS ENUM ('ANNUAL', 'PROBATION', 'PROJECT', 'PROMOTION', 'EXIT');
CREATE TYPE evaluation_status AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');
CREATE TYPE training_type AS ENUM ('INTERNAL', 'EXTERNAL', 'ONLINE', 'ON_THE_JOB', 'CERTIFICATION');
CREATE TYPE training_status AS ENUM ('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED');

-- ============================================================================
-- ORGANISATION
-- ============================================================================

-- Départements
CREATE TABLE hr_departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parent_id UUID REFERENCES hr_departments(id),
    manager_id UUID,  -- Référence vers hr_employees (ajouté après création de la table)
    cost_center VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_department_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_departments_tenant ON hr_departments(tenant_id);
CREATE INDEX idx_departments_parent ON hr_departments(tenant_id, parent_id);

-- Postes/Fonctions
CREATE TABLE hr_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    department_id UUID REFERENCES hr_departments(id),
    category VARCHAR(50),  -- CADRE, NON_CADRE, etc.
    level INTEGER DEFAULT 1,
    min_salary DECIMAL(12, 2),
    max_salary DECIMAL(12, 2),
    requirements JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_position_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_positions_tenant ON hr_positions(tenant_id);
CREATE INDEX idx_positions_department ON hr_positions(tenant_id, department_id);

-- ============================================================================
-- EMPLOYÉS
-- ============================================================================

CREATE TABLE hr_employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Identifiants
    employee_number VARCHAR(50) NOT NULL,
    user_id INTEGER,  -- Lien vers User si existe

    -- Informations personnelles
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    maiden_name VARCHAR(100),
    gender VARCHAR(10),
    birth_date DATE,
    birth_place VARCHAR(255),
    nationality VARCHAR(100),
    social_security_number VARCHAR(50),

    -- Contact
    email VARCHAR(255),
    personal_email VARCHAR(255),
    phone VARCHAR(50),
    mobile VARCHAR(50),

    -- Adresse
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    postal_code VARCHAR(20),
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'France',

    -- Organisation
    department_id UUID REFERENCES hr_departments(id),
    position_id UUID REFERENCES hr_positions(id),
    manager_id UUID REFERENCES hr_employees(id),
    work_location VARCHAR(255),

    -- Contrat actuel
    status employee_status DEFAULT 'ACTIVE',
    contract_type contract_type,
    hire_date DATE,
    start_date DATE,
    end_date DATE,
    seniority_date DATE,
    probation_end_date DATE,

    -- Rémunération
    gross_salary DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    pay_frequency VARCHAR(20) DEFAULT 'MONTHLY',

    -- Temps de travail
    weekly_hours DECIMAL(5, 2) DEFAULT 35.0,
    work_schedule VARCHAR(50),

    -- Congés
    annual_leave_balance DECIMAL(5, 2) DEFAULT 0,
    rtt_balance DECIMAL(5, 2) DEFAULT 0,

    -- Banque
    bank_name VARCHAR(255),
    iban VARCHAR(50),
    bic VARCHAR(20),

    -- Photo
    photo_url VARCHAR(500),

    -- Métadonnées
    notes TEXT,
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_employee_number UNIQUE (tenant_id, employee_number)
);

CREATE INDEX idx_employees_tenant ON hr_employees(tenant_id);
CREATE INDEX idx_employees_department ON hr_employees(tenant_id, department_id);
CREATE INDEX idx_employees_manager ON hr_employees(tenant_id, manager_id);
CREATE INDEX idx_employees_status ON hr_employees(tenant_id, status);
CREATE INDEX idx_employees_hire_date ON hr_employees(tenant_id, hire_date);

-- Ajouter la référence manager_id dans hr_departments après création de hr_employees
ALTER TABLE hr_departments ADD CONSTRAINT fk_department_manager
    FOREIGN KEY (manager_id) REFERENCES hr_employees(id);

-- ============================================================================
-- CONTRATS
-- ============================================================================

CREATE TABLE hr_contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),

    contract_number VARCHAR(50) NOT NULL,
    type contract_type NOT NULL,
    title VARCHAR(255),
    department_id UUID REFERENCES hr_departments(id),
    position_id UUID REFERENCES hr_positions(id),

    -- Dates
    start_date DATE NOT NULL,
    end_date DATE,  -- NULL pour CDI
    probation_duration INTEGER,  -- En jours
    probation_end_date DATE,
    signed_date DATE,

    -- Rémunération
    gross_salary DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    pay_frequency VARCHAR(20) DEFAULT 'MONTHLY',
    bonus_clause TEXT,

    -- Temps de travail
    weekly_hours DECIMAL(5, 2) DEFAULT 35.0,
    work_schedule VARCHAR(50) DEFAULT 'FULL_TIME',
    remote_work_policy VARCHAR(100),

    -- Conditions
    notice_period INTEGER,  -- En jours
    non_compete_clause BOOLEAN DEFAULT FALSE,
    confidentiality_clause BOOLEAN DEFAULT TRUE,

    -- Statut
    is_current BOOLEAN DEFAULT TRUE,
    terminated_date DATE,
    termination_reason VARCHAR(255),

    -- Documents
    document_url VARCHAR(500),

    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_contract_number UNIQUE (tenant_id, contract_number)
);

CREATE INDEX idx_contracts_tenant ON hr_contracts(tenant_id);
CREATE INDEX idx_contracts_employee ON hr_contracts(tenant_id, employee_id);
CREATE INDEX idx_contracts_current ON hr_contracts(tenant_id, is_current);

-- ============================================================================
-- CONGÉS
-- ============================================================================

CREATE TABLE hr_leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),

    type leave_type NOT NULL,
    status leave_status DEFAULT 'PENDING',

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_half_day BOOLEAN DEFAULT FALSE,
    end_half_day BOOLEAN DEFAULT FALSE,
    days_count DECIMAL(5, 2) NOT NULL,

    reason TEXT,
    attachment_url VARCHAR(500),

    -- Approbation
    approved_by UUID,
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- Remplacement
    replacement_id UUID REFERENCES hr_employees(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leaves_tenant ON hr_leave_requests(tenant_id);
CREATE INDEX idx_leaves_employee ON hr_leave_requests(tenant_id, employee_id);
CREATE INDEX idx_leaves_status ON hr_leave_requests(tenant_id, status);
CREATE INDEX idx_leaves_dates ON hr_leave_requests(tenant_id, start_date, end_date);

-- Soldes de congés
CREATE TABLE hr_leave_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),
    year INTEGER NOT NULL,
    leave_type leave_type NOT NULL,

    entitled_days DECIMAL(5, 2) DEFAULT 0,
    taken_days DECIMAL(5, 2) DEFAULT 0,
    pending_days DECIMAL(5, 2) DEFAULT 0,
    remaining_days DECIMAL(5, 2) DEFAULT 0,
    carried_over DECIMAL(5, 2) DEFAULT 0,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_leave_balance UNIQUE (tenant_id, employee_id, year, leave_type)
);

CREATE INDEX idx_leave_balances_tenant ON hr_leave_balances(tenant_id);
CREATE INDEX idx_leave_balances_employee ON hr_leave_balances(tenant_id, employee_id);

-- ============================================================================
-- PAIE
-- ============================================================================

-- Périodes de paie
CREATE TABLE hr_payroll_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    name VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    payment_date DATE,

    status payroll_status DEFAULT 'DRAFT',
    is_closed BOOLEAN DEFAULT FALSE,
    closed_at TIMESTAMP,
    closed_by UUID,

    total_gross DECIMAL(15, 2) DEFAULT 0,
    total_net DECIMAL(15, 2) DEFAULT 0,
    total_employer_charges DECIMAL(15, 2) DEFAULT 0,
    employee_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_payroll_period UNIQUE (tenant_id, year, month)
);

CREATE INDEX idx_payroll_periods_tenant ON hr_payroll_periods(tenant_id);
CREATE INDEX idx_payroll_periods_year ON hr_payroll_periods(tenant_id, year);

-- Bulletins de paie
CREATE TABLE hr_payslips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),
    period_id UUID NOT NULL REFERENCES hr_payroll_periods(id),

    payslip_number VARCHAR(50) NOT NULL,
    status payroll_status DEFAULT 'DRAFT',

    -- Période
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    payment_date DATE,

    -- Heures
    worked_hours DECIMAL(6, 2) DEFAULT 0,
    overtime_hours DECIMAL(6, 2) DEFAULT 0,
    absence_hours DECIMAL(6, 2) DEFAULT 0,

    -- Montants
    gross_salary DECIMAL(12, 2) NOT NULL,
    total_gross DECIMAL(12, 2) DEFAULT 0,
    total_deductions DECIMAL(12, 2) DEFAULT 0,
    employee_charges DECIMAL(12, 2) DEFAULT 0,
    employer_charges DECIMAL(12, 2) DEFAULT 0,
    taxable_income DECIMAL(12, 2) DEFAULT 0,
    tax_withheld DECIMAL(12, 2) DEFAULT 0,
    net_before_tax DECIMAL(12, 2) DEFAULT 0,
    net_salary DECIMAL(12, 2) DEFAULT 0,

    -- Cumuls annuels
    ytd_gross DECIMAL(15, 2) DEFAULT 0,
    ytd_net DECIMAL(15, 2) DEFAULT 0,
    ytd_tax DECIMAL(15, 2) DEFAULT 0,

    -- Document
    document_url VARCHAR(500),
    sent_at TIMESTAMP,

    validated_by UUID,
    validated_at TIMESTAMP,
    paid_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_payslip_number UNIQUE (tenant_id, payslip_number)
);

CREATE INDEX idx_payslips_tenant ON hr_payslips(tenant_id);
CREATE INDEX idx_payslips_employee ON hr_payslips(tenant_id, employee_id);
CREATE INDEX idx_payslips_period ON hr_payslips(tenant_id, period_id);
CREATE INDEX idx_payslips_status ON hr_payslips(tenant_id, status);

-- Lignes de bulletin
CREATE TABLE hr_payslip_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    payslip_id UUID NOT NULL REFERENCES hr_payslips(id) ON DELETE CASCADE,

    line_number INTEGER NOT NULL,
    type pay_element_type NOT NULL,
    code VARCHAR(50) NOT NULL,
    label VARCHAR(255) NOT NULL,

    base DECIMAL(12, 2),
    rate DECIMAL(8, 4),
    quantity DECIMAL(8, 2),
    amount DECIMAL(12, 2) NOT NULL,

    is_deduction BOOLEAN DEFAULT FALSE,
    is_employer_charge BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payslip_lines_payslip ON hr_payslip_lines(payslip_id);
CREATE INDEX idx_payslip_lines_tenant ON hr_payslip_lines(tenant_id);

-- ============================================================================
-- TEMPS DE TRAVAIL
-- ============================================================================

CREATE TABLE hr_time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),

    date DATE NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    break_duration INTEGER DEFAULT 0,  -- En minutes
    worked_hours DECIMAL(5, 2) NOT NULL,
    overtime_hours DECIMAL(5, 2) DEFAULT 0,

    project_id UUID,
    task_description VARCHAR(500),

    is_approved BOOLEAN DEFAULT FALSE,
    approved_by UUID,
    approved_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_time_entries_tenant ON hr_time_entries(tenant_id);
CREATE INDEX idx_time_entries_employee ON hr_time_entries(tenant_id, employee_id);
CREATE INDEX idx_time_entries_date ON hr_time_entries(tenant_id, date);

-- ============================================================================
-- COMPÉTENCES
-- ============================================================================

CREATE TABLE hr_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_skill_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_skills_tenant ON hr_skills(tenant_id);
CREATE INDEX idx_skills_category ON hr_skills(tenant_id, category);

CREATE TABLE hr_employee_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),
    skill_id UUID NOT NULL REFERENCES hr_skills(id),

    level INTEGER DEFAULT 1,  -- 1-5
    acquired_date DATE,
    expiry_date DATE,
    certification_url VARCHAR(500),
    notes TEXT,

    validated_by UUID,
    validated_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_employee_skill UNIQUE (tenant_id, employee_id, skill_id)
);

CREATE INDEX idx_employee_skills_tenant ON hr_employee_skills(tenant_id);
CREATE INDEX idx_employee_skills_employee ON hr_employee_skills(tenant_id, employee_id);

-- ============================================================================
-- FORMATIONS
-- ============================================================================

CREATE TABLE hr_trainings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,

    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type training_type NOT NULL,
    status training_status DEFAULT 'PLANNED',

    provider VARCHAR(255),
    trainer VARCHAR(255),
    location VARCHAR(255),

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_hours DECIMAL(6, 2),

    max_participants INTEGER,
    cost_per_person DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),

    skills_acquired JSONB DEFAULT '[]',

    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_training_code UNIQUE (tenant_id, code)
);

CREATE INDEX idx_trainings_tenant ON hr_trainings(tenant_id);
CREATE INDEX idx_trainings_dates ON hr_trainings(tenant_id, start_date, end_date);
CREATE INDEX idx_trainings_status ON hr_trainings(tenant_id, status);

CREATE TABLE hr_training_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    training_id UUID NOT NULL REFERENCES hr_trainings(id),
    employee_id UUID NOT NULL REFERENCES hr_employees(id),

    status VARCHAR(50) DEFAULT 'ENROLLED',
    attendance_rate DECIMAL(5, 2),
    score DECIMAL(5, 2),
    passed BOOLEAN,
    certificate_url VARCHAR(500),
    feedback TEXT,

    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    CONSTRAINT unique_training_participant UNIQUE (tenant_id, training_id, employee_id)
);

CREATE INDEX idx_training_participants_tenant ON hr_training_participants(tenant_id);
CREATE INDEX idx_training_participants_training ON hr_training_participants(training_id);
CREATE INDEX idx_training_participants_employee ON hr_training_participants(employee_id);

-- ============================================================================
-- ÉVALUATIONS
-- ============================================================================

CREATE TABLE hr_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),

    type evaluation_type NOT NULL,
    status evaluation_status DEFAULT 'SCHEDULED',

    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    scheduled_date DATE,
    completed_date DATE,

    evaluator_id UUID REFERENCES hr_employees(id),

    -- Scores (1-5 ou pourcentage)
    overall_score DECIMAL(5, 2),
    objectives_score DECIMAL(5, 2),
    skills_score DECIMAL(5, 2),
    behavior_score DECIMAL(5, 2),

    -- Contenu
    objectives_achieved JSONB DEFAULT '[]',
    objectives_next JSONB DEFAULT '[]',
    strengths TEXT,
    improvements TEXT,
    employee_comments TEXT,
    evaluator_comments TEXT,

    -- Recommandations
    promotion_recommended BOOLEAN DEFAULT FALSE,
    salary_increase_recommended BOOLEAN DEFAULT FALSE,
    training_needs JSONB DEFAULT '[]',

    -- Signatures
    employee_signed_at TIMESTAMP,
    evaluator_signed_at TIMESTAMP,

    document_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evaluations_tenant ON hr_evaluations(tenant_id);
CREATE INDEX idx_evaluations_employee ON hr_evaluations(tenant_id, employee_id);
CREATE INDEX idx_evaluations_status ON hr_evaluations(tenant_id, status);
CREATE INDEX idx_evaluations_scheduled ON hr_evaluations(tenant_id, scheduled_date);

-- ============================================================================
-- DOCUMENTS RH
-- ============================================================================

CREATE TABLE hr_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    employee_id UUID NOT NULL REFERENCES hr_employees(id),

    type hr_document_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_url VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),

    issue_date DATE,
    expiry_date DATE,
    is_confidential BOOLEAN DEFAULT FALSE,

    uploaded_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hr_documents_tenant ON hr_documents(tenant_id);
CREATE INDEX idx_hr_documents_employee ON hr_documents(tenant_id, employee_id);
CREATE INDEX idx_hr_documents_type ON hr_documents(tenant_id, type);
CREATE INDEX idx_hr_documents_expiry ON hr_documents(tenant_id, expiry_date);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger updated_at pour hr_departments
CREATE TRIGGER set_updated_at_hr_departments
    BEFORE UPDATE ON hr_departments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_positions
CREATE TRIGGER set_updated_at_hr_positions
    BEFORE UPDATE ON hr_positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_employees
CREATE TRIGGER set_updated_at_hr_employees
    BEFORE UPDATE ON hr_employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_contracts
CREATE TRIGGER set_updated_at_hr_contracts
    BEFORE UPDATE ON hr_contracts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_leave_requests
CREATE TRIGGER set_updated_at_hr_leave_requests
    BEFORE UPDATE ON hr_leave_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_payroll_periods
CREATE TRIGGER set_updated_at_hr_payroll_periods
    BEFORE UPDATE ON hr_payroll_periods
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_payslips
CREATE TRIGGER set_updated_at_hr_payslips
    BEFORE UPDATE ON hr_payslips
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_time_entries
CREATE TRIGGER set_updated_at_hr_time_entries
    BEFORE UPDATE ON hr_time_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_employee_skills
CREATE TRIGGER set_updated_at_hr_employee_skills
    BEFORE UPDATE ON hr_employee_skills
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_trainings
CREATE TRIGGER set_updated_at_hr_trainings
    BEFORE UPDATE ON hr_trainings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger updated_at pour hr_evaluations
CREATE TRIGGER set_updated_at_hr_evaluations
    BEFORE UPDATE ON hr_evaluations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FIN MIGRATION M3 - RH
-- ============================================================================
