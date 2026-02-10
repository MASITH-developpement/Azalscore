-- AZALS - ROLLBACK Migration Projects Module (M9)
-- Annule la creation des tables de gestion de projets

DO $$
BEGIN
    -- Drop triggers (created via dynamic SQL loop in UP migration)
    DROP TRIGGER IF EXISTS trg_project_templates_updated_at ON project_templates;
    DROP TRIGGER IF EXISTS trg_project_comments_updated_at ON project_comments;
    DROP TRIGGER IF EXISTS trg_project_documents_updated_at ON project_documents;
    DROP TRIGGER IF EXISTS trg_project_expenses_updated_at ON project_expenses;
    DROP TRIGGER IF EXISTS trg_project_budget_lines_updated_at ON project_budget_lines;
    DROP TRIGGER IF EXISTS trg_project_budgets_updated_at ON project_budgets;
    DROP TRIGGER IF EXISTS trg_project_time_entries_updated_at ON project_time_entries;
    DROP TRIGGER IF EXISTS trg_project_issues_updated_at ON project_issues;
    DROP TRIGGER IF EXISTS trg_project_risks_updated_at ON project_risks;
    DROP TRIGGER IF EXISTS trg_project_team_members_updated_at ON project_team_members;
    DROP TRIGGER IF EXISTS trg_project_milestones_updated_at ON project_milestones;
    DROP TRIGGER IF EXISTS trg_project_tasks_updated_at ON project_tasks;
    DROP TRIGGER IF EXISTS trg_project_phases_updated_at ON project_phases;
    DROP TRIGGER IF EXISTS trg_projects_updated_at ON projects;

    -- Drop function
    DROP FUNCTION IF EXISTS update_projects_updated_at();

    -- Drop indexes for project_kpis
    DROP INDEX IF EXISTS ix_project_kpis_date;
    DROP INDEX IF EXISTS ix_project_kpis_project;

    -- Drop indexes for project_comments
    DROP INDEX IF EXISTS ix_project_comments_task;
    DROP INDEX IF EXISTS ix_project_comments_project;

    -- Drop indexes for project_documents
    DROP INDEX IF EXISTS ix_project_documents_category;
    DROP INDEX IF EXISTS ix_project_documents_project;

    -- Drop indexes for project_expenses
    DROP INDEX IF EXISTS ix_project_expenses_status;
    DROP INDEX IF EXISTS ix_project_expenses_project;

    -- Drop indexes for project_budget_lines
    DROP INDEX IF EXISTS ix_budget_lines_budget;

    -- Drop indexes for project_budgets
    DROP INDEX IF EXISTS ix_project_budgets_project;

    -- Drop indexes for project_time_entries
    DROP INDEX IF EXISTS ix_project_time_status;
    DROP INDEX IF EXISTS ix_project_time_date;
    DROP INDEX IF EXISTS ix_project_time_user;
    DROP INDEX IF EXISTS ix_project_time_project;

    -- Drop indexes for project_issues
    DROP INDEX IF EXISTS ix_project_issues_assignee;
    DROP INDEX IF EXISTS ix_project_issues_status;
    DROP INDEX IF EXISTS ix_project_issues_project;

    -- Drop indexes for project_risks
    DROP INDEX IF EXISTS ix_project_risks_status;
    DROP INDEX IF EXISTS ix_project_risks_project;

    -- Drop indexes for project_team_members
    DROP INDEX IF EXISTS ix_project_team_unique;
    DROP INDEX IF EXISTS ix_project_team_user;
    DROP INDEX IF EXISTS ix_project_team_project;

    -- Drop indexes for project_milestones
    DROP INDEX IF EXISTS ix_project_milestones_date;
    DROP INDEX IF EXISTS ix_project_milestones_project;

    -- Drop indexes for task_dependencies
    DROP INDEX IF EXISTS ix_task_deps_successor;
    DROP INDEX IF EXISTS ix_task_deps_predecessor;

    -- Drop indexes for project_tasks
    DROP INDEX IF EXISTS ix_project_tasks_status;
    DROP INDEX IF EXISTS ix_project_tasks_assignee;
    DROP INDEX IF EXISTS ix_project_tasks_phase;
    DROP INDEX IF EXISTS ix_project_tasks_project;

    -- Drop indexes for project_phases
    DROP INDEX IF EXISTS ix_project_phases_project;

    -- Drop indexes for projects
    DROP INDEX IF EXISTS ix_projects_manager;
    DROP INDEX IF EXISTS ix_projects_tenant_status;
    DROP INDEX IF EXISTS ix_projects_tenant_code;

    -- Drop indexes for project_templates
    DROP INDEX IF EXISTS ix_project_templates_tenant;

    -- Drop tables in reverse order of dependencies
    DROP TABLE IF EXISTS project_kpis CASCADE;
    DROP TABLE IF EXISTS project_comments CASCADE;
    DROP TABLE IF EXISTS project_documents CASCADE;
    DROP TABLE IF EXISTS project_expenses CASCADE;
    DROP TABLE IF EXISTS project_budget_lines CASCADE;
    DROP TABLE IF EXISTS project_budgets CASCADE;
    DROP TABLE IF EXISTS project_time_entries CASCADE;
    DROP TABLE IF EXISTS project_issues CASCADE;
    DROP TABLE IF EXISTS project_risks CASCADE;
    DROP TABLE IF EXISTS project_team_members CASCADE;
    DROP TABLE IF EXISTS project_milestones CASCADE;
    DROP TABLE IF EXISTS task_dependencies CASCADE;
    DROP TABLE IF EXISTS project_tasks CASCADE;
    DROP TABLE IF EXISTS project_phases CASCADE;
    DROP TABLE IF EXISTS projects CASCADE;
    DROP TABLE IF EXISTS project_templates CASCADE;

    -- Drop ENUM types (after tables that use them)
    DROP TYPE IF EXISTS budget_type_proj;
    DROP TYPE IF EXISTS expense_status_proj;
    DROP TYPE IF EXISTS time_entry_status;
    DROP TYPE IF EXISTS team_member_role;
    DROP TYPE IF EXISTS issue_priority_proj;
    DROP TYPE IF EXISTS issue_status_proj;
    DROP TYPE IF EXISTS risk_probability;
    DROP TYPE IF EXISTS risk_impact;
    DROP TYPE IF EXISTS risk_status;
    DROP TYPE IF EXISTS milestone_status;
    DROP TYPE IF EXISTS task_priority_proj;
    DROP TYPE IF EXISTS task_status_proj;
    DROP TYPE IF EXISTS project_priority;
    DROP TYPE IF EXISTS project_status;

    RAISE NOTICE 'Migration 024_projects_module rolled back successfully';
END $$;
