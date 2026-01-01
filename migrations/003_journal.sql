-- AZALS - Journal APPEND-ONLY
-- Table journal_entries avec protections UPDATE/DELETE par triggers

CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performance
CREATE INDEX idx_journal_tenant_id ON journal_entries(tenant_id);
CREATE INDEX idx_journal_user_id ON journal_entries(user_id);
CREATE INDEX idx_journal_tenant_user ON journal_entries(tenant_id, user_id);
CREATE INDEX idx_journal_created_at ON journal_entries(created_at);

-- TRIGGER INTERDISANT UPDATE
-- Toute tentative de modification échoue immédiatement
CREATE OR REPLACE FUNCTION prevent_journal_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'UPDATE interdit sur journal_entries. Journal APPEND-ONLY.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prevent_journal_update
BEFORE UPDATE ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION prevent_journal_update();

-- TRIGGER INTERDISANT DELETE
-- Toute tentative de suppression échoue immédiatement
CREATE OR REPLACE FUNCTION prevent_journal_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'DELETE interdit sur journal_entries. Journal APPEND-ONLY.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prevent_journal_delete
BEFORE DELETE ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION prevent_journal_delete();
