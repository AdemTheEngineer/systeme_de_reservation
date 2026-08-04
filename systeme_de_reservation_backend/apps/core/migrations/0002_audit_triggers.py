"""Trigger d'audit générique (append-only, cf. NFR journalisation des
opérations sensibles : réservation, annulation, paiement).

Non exprimable via l'ORM Django : la fonction PL/pgSQL est paramétrée par
le nom de la colonne PK de la table cible (`TG_ARGV[0]`), pour rester
générique sans dépendre du nom de la clé primaire (`id_reservation` vs
`id`). Elle lit l'acteur/l'IP via `current_setting(...)`, positionnés par
`apps/core/middleware.py::AuditContextMiddleware` en tout début de requête.

`v_acteur` est un `bigint` (pas un `uuid`) : `Utilisateur` (AUTH_USER_MODEL)
garde le PK entier par défaut de `AbstractUser`.
"""

from django.db import migrations

CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION audit_log_trigger() RETURNS trigger AS $$
DECLARE
    v_acteur bigint;
    v_ip inet;
    v_donnees jsonb;
    v_row_id text;
BEGIN
    BEGIN
        v_acteur := NULLIF(current_setting('app.current_user_id', true), '')::bigint;
    EXCEPTION WHEN others THEN
        v_acteur := NULL;
    END;

    BEGIN
        v_ip := NULLIF(current_setting('app.client_ip', true), '')::inet;
    EXCEPTION WHEN others THEN
        v_ip := NULL;
    END;

    IF TG_OP = 'DELETE' THEN
        v_donnees := to_jsonb(OLD);
    ELSE
        v_donnees := to_jsonb(NEW);
    END IF;
    v_row_id := v_donnees ->> TG_ARGV[0];

    INSERT INTO audit_log (table_name, operation, row_id, acteur_id, ip, donnees, horodatage)
    VALUES (TG_TABLE_NAME, TG_OP, v_row_id, v_acteur, v_ip, v_donnees, now());

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""

DROP_FUNCTION = 'DROP FUNCTION IF EXISTS audit_log_trigger() CASCADE;'

CREATE_TRIGGERS = """
CREATE TRIGGER trg_audit_reservation
    AFTER INSERT OR UPDATE OR DELETE ON reservation
    FOR EACH ROW EXECUTE FUNCTION audit_log_trigger('id_reservation');

CREATE TRIGGER trg_audit_paiement
    AFTER INSERT OR UPDATE ON paiement
    FOR EACH ROW EXECUTE FUNCTION audit_log_trigger('id');
"""

DROP_TRIGGERS = """
DROP TRIGGER IF EXISTS trg_audit_reservation ON reservation;
DROP TRIGGER IF EXISTS trg_audit_paiement ON paiement;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('reservations', '0001_initial'),
        ('paiements', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_FUNCTION, reverse_sql=DROP_FUNCTION),
        migrations.RunSQL(sql=CREATE_TRIGGERS, reverse_sql=DROP_TRIGGERS),
    ]
