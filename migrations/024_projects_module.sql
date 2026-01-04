-- ============================================================================
-- AZALS ERP - MODULE M9: PROJETS (Project Management)
-- Migration SQL pour PostgreSQL
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE project_status AS ENUM (
        'draft', 'planning', 'approved', 'in_progress',
        'on_hold', 'completed', 'cancelled', 'archived'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE project_priority AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE task_status_proj AS ENUM (
        'todo', 'in_progress', 'review', 'blocked', 'completed', 'cancelled'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE task_priority_proj AS ENUM ('low', 'medium', 'high', 'urgent');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE milestone_status AS ENUM (
        'pending', 'in_progress', 'achieved', 'missed', 'cancelled'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_status AS ENUM (
        'identified', 'analyzing', 'mitigating', 'monitoring', 'occurred', 'closed'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_impact AS ENUM (
        'negligible', 'minor', 'moderate', 'major', 'critical'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE risk_probability AS ENUM (
        'rare', 'unlikely', 'possible', 'likely', 'almost_certain'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE issue_status_proj AS ENUM (
        'open', 'in_progress', 'pending', 'resolved', 'closed', 'wont_fix'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE issue_priority_proj AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE team_member_role AS ENUM (
        'project_manager', 'team_lead', 'member', 'stakeholder', 'consultant', 'observer'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE time_entry_status AS ENUM ('draft', 'submitted', 'approved', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE expense_status_proj AS ENUM ('draft', 'submitted', 'approved', 'rejected', 'paid');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE budget_type_proj AS ENUM ('capex', 'opex', 'mixed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ============================================================================
-- TABLE: project_templates (doit être créée avant projects)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,

    -- Identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Configuration par défaut
    default_priority project_priority DEFAULT 'medium',
    default_budget_type budget_type_proj,
    estimated_duration_days INTEGER,

    -- Structure (JSON)
    phases_template JSONB DEFAULT '[]'::jsonb,
    tasks_template JSONB DEFAULT '[]'::jsonb,
    milestones_template JSONB DEFAULT '[]'::jsonb,
    risks_template JSONB DEFAULT '[]'::jsonb,
    roles_template JSONB DEFAULT '[]'::jsonb,
    budget_template JSONB DEFAULT '[]'::jsonb,
    checklist JSONB DEFAULT '[]'::jsonb,
    settings JSONB DEFAULT '{}'::jsonb,

    -- Statut
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_templates_tenant ON project_templates(tenant_id);


-- ============================================================================
-- TABLE: projects
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,

    -- Identification
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Classification
    status project_status DEFAULT 'draft' NOT NULL,
    priority project_priority DEFAULT 'medium' NOT NULL,
    category VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,

    -- Dates
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,

    -- Responsables
    project_manager_id UUID,
    sponsor_id UUID,
    customer_id UUID,

    -- Budget
    budget_type budget_type_proj,
    planned_budget DECIMAL(15,2) DEFAULT 0,
    actual_cost DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Effort
    planned_hours FLOAT DEFAULT 0,
    actual_hours FLOAT DEFAULT 0,

    -- Progression
    progress_percent FLOAT DEFAULT 0,
    health_status VARCHAR(20),

    -- Hiérarchie
    parent_project_id UUID REFERENCES projects(id),
    template_id UUID REFERENCES project_templates(id),

    -- Paramètres
    is_billable BOOLEAN DEFAULT FALSE,
    billing_rate DECIMAL(10,2),
    allow_overtime BOOLEAN DEFAULT TRUE,
    require_time_approval BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}'::jsonb,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    archived_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_projects_tenant_code ON projects(tenant_id, code);
CREATE INDEX IF NOT EXISTS ix_projects_tenant_status ON projects(tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_projects_manager ON projects(tenant_id, project_manager_id);


-- ============================================================================
-- TABLE: project_phases
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    "order" INTEGER DEFAULT 0,
    color VARCHAR(20),

    -- Dates
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,

    -- Progression
    progress_percent FLOAT DEFAULT 0,
    status task_status_proj DEFAULT 'todo',

    -- Effort
    planned_hours FLOAT DEFAULT 0,
    actual_hours FLOAT DEFAULT 0,

    -- Budget
    planned_budget DECIMAL(15,2) DEFAULT 0,
    actual_cost DECIMAL(15,2) DEFAULT 0,

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_phases_project ON project_phases(project_id);


-- ============================================================================
-- TABLE: project_tasks
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES project_tasks(id) ON DELETE SET NULL,

    -- Identification
    code VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Classification
    status task_status_proj DEFAULT 'todo' NOT NULL,
    priority task_priority_proj DEFAULT 'medium' NOT NULL,
    task_type VARCHAR(50),
    tags JSONB DEFAULT '[]'::jsonb,

    -- Dates
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    due_date DATE,

    -- Assignation
    assignee_id UUID,
    reporter_id UUID,

    -- Effort
    estimated_hours FLOAT DEFAULT 0,
    actual_hours FLOAT DEFAULT 0,
    remaining_hours FLOAT DEFAULT 0,

    -- Progression
    progress_percent FLOAT DEFAULT 0,

    -- Hiérarchie
    "order" INTEGER DEFAULT 0,
    wbs_code VARCHAR(50),

    -- Options
    is_milestone BOOLEAN DEFAULT FALSE,
    is_critical BOOLEAN DEFAULT FALSE,
    is_billable BOOLEAN DEFAULT TRUE,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_tasks_project ON project_tasks(project_id);
CREATE INDEX IF NOT EXISTS ix_project_tasks_phase ON project_tasks(phase_id);
CREATE INDEX IF NOT EXISTS ix_project_tasks_assignee ON project_tasks(tenant_id, assignee_id);
CREATE INDEX IF NOT EXISTS ix_project_tasks_status ON project_tasks(tenant_id, status);


-- ============================================================================
-- TABLE: task_dependencies
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    predecessor_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    successor_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(10) DEFAULT 'FS',
    lag_days INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_task_deps_predecessor ON task_dependencies(predecessor_id);
CREATE INDEX IF NOT EXISTS ix_task_deps_successor ON task_dependencies(successor_id);


-- ============================================================================
-- TABLE: project_milestones
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(id) ON DELETE SET NULL,

    -- Identification
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Dates
    target_date DATE NOT NULL,
    actual_date DATE,

    -- Statut
    status milestone_status DEFAULT 'pending' NOT NULL,

    -- Importance
    is_key_milestone BOOLEAN DEFAULT FALSE,
    is_customer_visible BOOLEAN DEFAULT TRUE,

    -- Délivrables
    deliverables JSONB DEFAULT '[]'::jsonb,
    acceptance_criteria TEXT,

    -- Validation
    validated_by UUID,
    validated_at TIMESTAMP,
    validation_notes TEXT,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_milestones_project ON project_milestones(project_id);
CREATE INDEX IF NOT EXISTS ix_project_milestones_date ON project_milestones(tenant_id, target_date);


-- ============================================================================
-- TABLE: project_team_members
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Membre
    user_id UUID NOT NULL,
    employee_id UUID,

    -- Rôle
    role team_member_role DEFAULT 'member' NOT NULL,
    role_description VARCHAR(255),

    -- Allocation
    allocation_percent FLOAT DEFAULT 100,
    start_date DATE,
    end_date DATE,

    -- Tarification
    hourly_rate DECIMAL(10,2),
    daily_rate DECIMAL(10,2),
    is_billable BOOLEAN DEFAULT TRUE,

    -- Permissions projet
    can_log_time BOOLEAN DEFAULT TRUE,
    can_view_budget BOOLEAN DEFAULT FALSE,
    can_manage_tasks BOOLEAN DEFAULT FALSE,
    can_approve_time BOOLEAN DEFAULT FALSE,

    -- Notifications
    notify_on_task BOOLEAN DEFAULT TRUE,
    notify_on_milestone BOOLEAN DEFAULT TRUE,
    notify_on_issue BOOLEAN DEFAULT TRUE,

    -- Métadonnées
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_team_project ON project_team_members(project_id);
CREATE INDEX IF NOT EXISTS ix_project_team_user ON project_team_members(tenant_id, user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_project_team_unique ON project_team_members(project_id, user_id);


-- ============================================================================
-- TABLE: project_risks
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Identification
    code VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Évaluation
    status risk_status DEFAULT 'identified' NOT NULL,
    probability risk_probability NOT NULL,
    impact risk_impact NOT NULL,
    risk_score FLOAT,

    -- Impact financier
    estimated_impact_min DECIMAL(15,2),
    estimated_impact_max DECIMAL(15,2),

    -- Dates
    identified_date DATE DEFAULT CURRENT_DATE,
    review_date DATE,
    occurred_date DATE,
    closed_date DATE,

    -- Responsable
    owner_id UUID,

    -- Réponse
    response_strategy VARCHAR(50),
    mitigation_plan TEXT,
    contingency_plan TEXT,
    triggers JSONB DEFAULT '[]'::jsonb,

    -- Suivi
    monitoring_notes TEXT,
    last_review_date DATE,
    last_reviewed_by UUID,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_risks_project ON project_risks(project_id);
CREATE INDEX IF NOT EXISTS ix_project_risks_status ON project_risks(tenant_id, status);


-- ============================================================================
-- TABLE: project_issues
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES project_tasks(id) ON DELETE SET NULL,

    -- Identification
    code VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Statut
    status issue_status_proj DEFAULT 'open' NOT NULL,
    priority issue_priority_proj DEFAULT 'medium' NOT NULL,

    -- Personnes
    reporter_id UUID,
    assignee_id UUID,

    -- Dates
    reported_date DATE DEFAULT CURRENT_DATE,
    due_date DATE,
    resolved_date DATE,
    closed_date DATE,

    -- Impact
    impact_description TEXT,
    affected_areas JSONB DEFAULT '[]'::jsonb,

    -- Résolution
    resolution TEXT,
    resolution_type VARCHAR(50),

    -- Escalade
    is_escalated BOOLEAN DEFAULT FALSE,
    escalated_to_id UUID,
    escalation_date TIMESTAMP,
    escalation_reason TEXT,

    -- Lien risque
    related_risk_id UUID REFERENCES project_risks(id),

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_issues_project ON project_issues(project_id);
CREATE INDEX IF NOT EXISTS ix_project_issues_status ON project_issues(tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_project_issues_assignee ON project_issues(tenant_id, assignee_id);


-- ============================================================================
-- TABLE: project_time_entries
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES project_tasks(id) ON DELETE SET NULL,

    -- Utilisateur
    user_id UUID NOT NULL,
    employee_id UUID,

    -- Date et durée
    date DATE NOT NULL,
    hours FLOAT NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,

    -- Description
    description TEXT,
    activity_type VARCHAR(50),

    -- Statut
    status time_entry_status DEFAULT 'draft' NOT NULL,

    -- Facturation
    is_billable BOOLEAN DEFAULT TRUE,
    billing_rate DECIMAL(10,2),
    billing_amount DECIMAL(15,2),
    is_invoiced BOOLEAN DEFAULT FALSE,
    invoice_id UUID,

    -- Approbation
    approved_by UUID,
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- Overtime
    is_overtime BOOLEAN DEFAULT FALSE,
    overtime_rate FLOAT DEFAULT 1.5,

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_time_project ON project_time_entries(project_id);
CREATE INDEX IF NOT EXISTS ix_project_time_user ON project_time_entries(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS ix_project_time_date ON project_time_entries(tenant_id, date);
CREATE INDEX IF NOT EXISTS ix_project_time_status ON project_time_entries(tenant_id, status);


-- ============================================================================
-- TABLE: project_budgets
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    fiscal_year VARCHAR(4),
    version VARCHAR(20) DEFAULT '1.0',

    -- Type
    budget_type budget_type_proj DEFAULT 'mixed',

    -- Montants
    total_budget DECIMAL(15,2) DEFAULT 0,
    total_committed DECIMAL(15,2) DEFAULT 0,
    total_actual DECIMAL(15,2) DEFAULT 0,
    total_forecast DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Statut
    is_approved BOOLEAN DEFAULT FALSE,
    approved_by UUID,
    approved_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,

    -- Dates
    start_date DATE,
    end_date DATE,

    -- Métadonnées
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_budgets_project ON project_budgets(project_id);


-- ============================================================================
-- TABLE: project_budget_lines
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_budget_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    budget_id UUID NOT NULL REFERENCES project_budgets(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(id) ON DELETE SET NULL,

    -- Identification
    code VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Montants
    budget_amount DECIMAL(15,2) DEFAULT 0,
    committed_amount DECIMAL(15,2) DEFAULT 0,
    actual_amount DECIMAL(15,2) DEFAULT 0,
    forecast_amount DECIMAL(15,2) DEFAULT 0,

    -- Quantités
    quantity FLOAT,
    unit VARCHAR(20),
    unit_price DECIMAL(15,2),

    -- Hiérarchie
    "order" INTEGER DEFAULT 0,
    parent_line_id UUID REFERENCES project_budget_lines(id) ON DELETE SET NULL,

    -- Comptabilité
    account_code VARCHAR(20),

    -- Métadonnées
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_budget_lines_budget ON project_budget_lines(budget_id);


-- ============================================================================
-- TABLE: project_expenses
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES project_tasks(id) ON DELETE SET NULL,
    budget_line_id UUID REFERENCES project_budget_lines(id) ON DELETE SET NULL,

    -- Identification
    reference VARCHAR(100),
    description TEXT NOT NULL,
    category VARCHAR(100),

    -- Montant
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    quantity FLOAT DEFAULT 1,
    unit_price DECIMAL(15,2),

    -- Dates
    expense_date DATE NOT NULL,
    due_date DATE,
    paid_date DATE,

    -- Statut
    status expense_status_proj DEFAULT 'draft' NOT NULL,

    -- Personne
    submitted_by UUID,
    vendor VARCHAR(255),

    -- Approbation
    approved_by UUID,
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- Facturation
    is_billable BOOLEAN DEFAULT TRUE,
    is_invoiced BOOLEAN DEFAULT FALSE,
    invoice_id UUID,

    -- Pièces jointes
    receipt_url VARCHAR(500),
    attachments JSONB DEFAULT '[]'::jsonb,

    -- Métadonnées
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_project_expenses_project ON project_expenses(project_id);
CREATE INDEX IF NOT EXISTS ix_project_expenses_status ON project_expenses(tenant_id, status);


-- ============================================================================
-- TABLE: project_documents
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),

    -- Fichier
    file_name VARCHAR(255),
    file_url VARCHAR(500),
    file_size INTEGER,
    file_type VARCHAR(100),

    -- Versioning
    version VARCHAR(20) DEFAULT '1.0',
    is_latest BOOLEAN DEFAULT TRUE,
    previous_version_id UUID,

    -- Accès
    is_public BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(50) DEFAULT 'team',

    -- Métadonnées
    uploaded_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_project_documents_project ON project_documents(project_id);
CREATE INDEX IF NOT EXISTS ix_project_documents_category ON project_documents(tenant_id, category);


-- ============================================================================
-- TABLE: project_comments
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES project_tasks(id) ON DELETE CASCADE,

    -- Contenu
    content TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'comment',

    -- Réponse
    parent_comment_id UUID REFERENCES project_comments(id) ON DELETE CASCADE,

    -- Mentions et attachments
    mentions JSONB DEFAULT '[]'::jsonb,
    attachments JSONB DEFAULT '[]'::jsonb,

    -- Visibility
    is_internal BOOLEAN DEFAULT TRUE,

    -- Métadonnées
    author_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_edited BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_project_comments_project ON project_comments(project_id);
CREATE INDEX IF NOT EXISTS ix_project_comments_task ON project_comments(task_id);


-- ============================================================================
-- TABLE: project_kpis
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id INTEGER NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Identification
    kpi_date DATE NOT NULL,

    -- EVM (Earned Value Management)
    planned_value DECIMAL(15,2),
    earned_value DECIMAL(15,2),
    actual_cost DECIMAL(15,2),

    -- Indices
    schedule_variance DECIMAL(15,2),
    cost_variance DECIMAL(15,2),
    schedule_performance_index FLOAT,
    cost_performance_index FLOAT,

    -- Estimations
    estimate_at_completion DECIMAL(15,2),
    estimate_to_complete DECIMAL(15,2),
    variance_at_completion DECIMAL(15,2),

    -- Progression tâches
    tasks_total INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_in_progress INTEGER DEFAULT 0,
    tasks_blocked INTEGER DEFAULT 0,

    -- Effort
    hours_planned FLOAT DEFAULT 0,
    hours_actual FLOAT DEFAULT 0,
    hours_remaining FLOAT DEFAULT 0,

    -- Risques
    risks_total INTEGER DEFAULT 0,
    risks_open INTEGER DEFAULT 0,
    risks_high INTEGER DEFAULT 0,

    -- Issues
    issues_total INTEGER DEFAULT 0,
    issues_open INTEGER DEFAULT 0,
    issues_critical INTEGER DEFAULT 0,

    -- Qualité
    defects_found INTEGER DEFAULT 0,
    defects_fixed INTEGER DEFAULT 0,

    -- Métadonnées
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculated_by UUID
);

CREATE INDEX IF NOT EXISTS ix_project_kpis_project ON project_kpis(project_id);
CREATE INDEX IF NOT EXISTS ix_project_kpis_date ON project_kpis(project_id, kpi_date);


-- ============================================================================
-- TRIGGERS: updated_at automatique
-- ============================================================================

CREATE OR REPLACE FUNCTION update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour chaque table
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'projects', 'project_phases', 'project_tasks', 'project_milestones',
        'project_team_members', 'project_risks', 'project_issues',
        'project_time_entries', 'project_budgets', 'project_budget_lines',
        'project_expenses', 'project_documents', 'project_comments',
        'project_templates'
    ]
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS trg_%s_updated_at ON %s;
            CREATE TRIGGER trg_%s_updated_at
            BEFORE UPDATE ON %s
            FOR EACH ROW
            EXECUTE FUNCTION update_projects_updated_at();
        ', tbl, tbl, tbl, tbl);
    END LOOP;
END $$;


-- ============================================================================
-- COMMENTAIRES
-- ============================================================================

COMMENT ON TABLE projects IS 'Projets - gestion de projet avec phases, tâches et suivi';
COMMENT ON TABLE project_phases IS 'Phases de projet pour organiser les tâches';
COMMENT ON TABLE project_tasks IS 'Tâches de projet avec assignation et suivi';
COMMENT ON TABLE task_dependencies IS 'Dépendances entre tâches (FS, FF, SS, SF)';
COMMENT ON TABLE project_milestones IS 'Jalons projet avec dates cibles et délivrables';
COMMENT ON TABLE project_team_members IS 'Membres de l équipe projet avec rôles et allocation';
COMMENT ON TABLE project_risks IS 'Risques projet avec évaluation et plans de réponse';
COMMENT ON TABLE project_issues IS 'Issues et problèmes projet avec suivi résolution';
COMMENT ON TABLE project_time_entries IS 'Saisies de temps sur projets avec approbation';
COMMENT ON TABLE project_budgets IS 'Budgets projet avec lignes détaillées';
COMMENT ON TABLE project_budget_lines IS 'Lignes de budget par catégorie';
COMMENT ON TABLE project_expenses IS 'Dépenses projet avec approbation';
COMMENT ON TABLE project_documents IS 'Documents projet avec versioning';
COMMENT ON TABLE project_comments IS 'Commentaires sur projets et tâches';
COMMENT ON TABLE project_kpis IS 'KPIs projet (EVM) calculés périodiquement';
COMMENT ON TABLE project_templates IS 'Templates pour création de projets';
