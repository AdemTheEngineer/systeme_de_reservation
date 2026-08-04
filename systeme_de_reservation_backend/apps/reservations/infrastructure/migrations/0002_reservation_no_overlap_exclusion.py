"""Contrainte anti-chevauchement au niveau SGBD (défense en profondeur).

Non exprimable via l'ORM Django : ajoutée en RunSQL, après activation de
l'extension PostgreSQL `btree_gist`. Scope volontairement restreint à
`statut = 'CONFIRMEE'` (et non EN_ATTENTE aussi) : cohérent avec la règle
du domaine (`Reservation.verifier_chevauchement`, cf. domain/entities.py)
où seule une réservation CONFIRMEE bloque un créneau. C'est le filet de
sécurité en cas de course entre deux confirmations concurrentes.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS btree_gist;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE reservation
                    ADD CONSTRAINT ex_reservation_no_overlap
                    EXCLUDE USING gist (
                        id_espace WITH =,
                        tstzrange(date_debut, date_fin) WITH &&
                    ) WHERE (statut = 'CONFIRMEE');
            """,
            reverse_sql='ALTER TABLE reservation DROP CONSTRAINT ex_reservation_no_overlap;',
        ),
    ]
