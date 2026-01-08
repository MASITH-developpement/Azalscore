-- AZALS - Migration Hash Chaîné Journal d'Audit
-- ==============================================
-- Ajoute un hash cryptographique chaîné pour garantir l'intégrité du journal.
-- Chaque entrée contient le hash de l'entrée précédente.
-- Modification = rupture de chaîne = détection immédiate.

-- Ajout des colonnes de hash
ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64);
ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS entry_hash VARCHAR(64);

-- Index sur entry_hash pour vérification rapide
CREATE INDEX IF NOT EXISTS idx_journal_entry_hash ON journal_entries(entry_hash);
CREATE INDEX IF NOT EXISTS idx_journal_previous_hash ON journal_entries(previous_hash);

-- Fonction de calcul du hash pour nouvelles entrées
CREATE OR REPLACE FUNCTION calculate_journal_hash()
RETURNS TRIGGER AS $$
DECLARE
    prev_hash VARCHAR(64);
    hash_input TEXT;
BEGIN
    -- Récupérer le hash de l'entrée précédente pour ce tenant
    SELECT entry_hash INTO prev_hash
    FROM journal_entries
    WHERE tenant_id = NEW.tenant_id
    ORDER BY id DESC
    LIMIT 1;

    -- Si première entrée du tenant, utiliser un bloc genesis
    IF prev_hash IS NULL THEN
        prev_hash := 'GENESIS_' || encode(sha256(NEW.tenant_id::bytea), 'hex');
    END IF;

    -- Stocker le hash précédent
    NEW.previous_hash := prev_hash;

    -- Calculer le hash de cette entrée
    -- Inclut: tenant_id, user_id, action, details, created_at, previous_hash
    hash_input := CONCAT(
        NEW.tenant_id, '|',
        NEW.user_id::text, '|',
        NEW.action, '|',
        COALESCE(NEW.details, ''), '|',
        EXTRACT(EPOCH FROM NEW.created_at)::text, '|',
        prev_hash
    );

    NEW.entry_hash := encode(sha256(hash_input::bytea), 'hex');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour calculer automatiquement le hash
DROP TRIGGER IF EXISTS trigger_calculate_journal_hash ON journal_entries;
CREATE TRIGGER trigger_calculate_journal_hash
BEFORE INSERT ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION calculate_journal_hash();

-- Fonction de vérification d'intégrité pour un tenant
CREATE OR REPLACE FUNCTION verify_journal_integrity(p_tenant_id VARCHAR(255))
RETURNS TABLE (
    is_valid BOOLEAN,
    broken_at_id INTEGER,
    expected_hash VARCHAR(64),
    actual_hash VARCHAR(64),
    entries_checked INTEGER
) AS $$
DECLARE
    v_entry RECORD;
    v_prev_hash VARCHAR(64);
    v_calculated_hash VARCHAR(64);
    v_hash_input TEXT;
    v_count INTEGER := 0;
BEGIN
    -- Initialiser le hash genesis
    v_prev_hash := 'GENESIS_' || encode(sha256(p_tenant_id::bytea), 'hex');

    -- Parcourir toutes les entrées du tenant dans l'ordre
    FOR v_entry IN
        SELECT * FROM journal_entries
        WHERE tenant_id = p_tenant_id
        ORDER BY id ASC
    LOOP
        v_count := v_count + 1;

        -- Vérifier le hash précédent
        IF v_entry.previous_hash != v_prev_hash THEN
            RETURN QUERY SELECT
                FALSE,
                v_entry.id,
                v_prev_hash,
                v_entry.previous_hash,
                v_count;
            RETURN;
        END IF;

        -- Recalculer le hash de cette entrée
        v_hash_input := CONCAT(
            v_entry.tenant_id, '|',
            v_entry.user_id::text, '|',
            v_entry.action, '|',
            COALESCE(v_entry.details, ''), '|',
            EXTRACT(EPOCH FROM v_entry.created_at)::text, '|',
            v_entry.previous_hash
        );
        v_calculated_hash := encode(sha256(v_hash_input::bytea), 'hex');

        -- Vérifier le hash de l'entrée
        IF v_entry.entry_hash != v_calculated_hash THEN
            RETURN QUERY SELECT
                FALSE,
                v_entry.id,
                v_calculated_hash,
                v_entry.entry_hash,
                v_count;
            RETURN;
        END IF;

        -- Mettre à jour pour l'itération suivante
        v_prev_hash := v_entry.entry_hash;
    END LOOP;

    -- Tout est valide
    RETURN QUERY SELECT TRUE, NULL::INTEGER, NULL::VARCHAR(64), NULL::VARCHAR(64), v_count;
END;
$$ LANGUAGE plpgsql;

-- Migration des entrées existantes (calcul du hash pour les anciennes entrées)
-- Note: Exécuter une seule fois avec DO block
DO $$
DECLARE
    v_entry RECORD;
    v_prev_hash VARCHAR(64);
    v_hash_input TEXT;
    v_current_tenant VARCHAR(255) := '';
BEGIN
    FOR v_entry IN
        SELECT * FROM journal_entries
        WHERE entry_hash IS NULL
        ORDER BY tenant_id, id ASC
    LOOP
        -- Reset du hash genesis si nouveau tenant
        IF v_current_tenant != v_entry.tenant_id THEN
            v_current_tenant := v_entry.tenant_id;
            v_prev_hash := 'GENESIS_' || encode(sha256(v_current_tenant::bytea), 'hex');
        END IF;

        -- Calculer et mettre à jour
        v_hash_input := CONCAT(
            v_entry.tenant_id, '|',
            v_entry.user_id::text, '|',
            v_entry.action, '|',
            COALESCE(v_entry.details, ''), '|',
            EXTRACT(EPOCH FROM v_entry.created_at)::text, '|',
            v_prev_hash
        );

        UPDATE journal_entries
        SET previous_hash = v_prev_hash,
            entry_hash = encode(sha256(v_hash_input::bytea), 'hex')
        WHERE id = v_entry.id;

        -- Récupérer le hash pour la prochaine itération
        SELECT entry_hash INTO v_prev_hash FROM journal_entries WHERE id = v_entry.id;
    END LOOP;
END $$;

-- Commentaires pour documentation
COMMENT ON COLUMN journal_entries.previous_hash IS 'Hash SHA-256 de l entrée précédente - garantit le chaînage';
COMMENT ON COLUMN journal_entries.entry_hash IS 'Hash SHA-256 de cette entrée - garantit l intégrité';
COMMENT ON FUNCTION verify_journal_integrity(VARCHAR) IS 'Vérifie l intégrité du journal d audit pour un tenant';
