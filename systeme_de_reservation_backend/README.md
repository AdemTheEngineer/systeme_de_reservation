# Système de réservation de salles de coworking — backend

Backend Django/DRF pour un système privé de réservation de salles de coworking,
structuré en Domain-Driven Design (4 couches complètes pour le contexte cœur
`reservations` ; contextes support `identite` et `paiements` plus légers).
Une seule base PostgreSQL partagée (`systeme_reservation_db`), FKs
inter-contextes autorisées.

## Bounded contexts

- `apps/core` — Shared Kernel : classes de base du domaine (`Entity`,
  `ValueObject`, `DomainEvent`), dispatcher d'événements in-process, table
  d'audit + trigger.
- `apps/reservations` — cœur du domaine : `domain/` (Entities, VOs, Aggregate
  Root `Reservation`, exceptions, repositories abstraits, events),
  `application/` (use cases), `infrastructure/` (modèles ORM, mappers,
  repositories concrets), `interfaces/` (DRF).
- `apps/identite` — `Utilisateur` (AUTH_USER_MODEL, connexion par email),
  `Membre`, `Gestionnaire`, JWT.
- `apps/paiements` — paiement simulé (mock, pas de vraie passerelle).

## Prérequis

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (aucune commande `pip` n'est utilisée dans ce projet)
- PostgreSQL 14+ (extension `btree_gist` — activée automatiquement par une migration)

## Installation (sans Docker)

```bash
uv sync

cp .env.example .env
# Éditer .env : DB_NAME/DB_USER/DB_PASSWORD doivent correspondre à une base
# PostgreSQL existante (créée manuellement au préalable, `uv run manage.py
# migrate` ne crée pas la base elle-même).

uv run python manage.py migrate
uv run python manage.py createsuperuser  # optionnel, pour /admin/
uv run python manage.py runserver
```

L'API est servie sur `http://localhost:8000/api/v2/`, l'admin Django sur
`http://localhost:8000/admin/`.

## Installation (Docker Compose)

```bash
cp .env.example .env
docker compose up --build
```

Le service `backend` attend que `postgres` soit prêt (healthcheck), applique
les migrations automatiquement puis démarre `runserver` sur le port 8000.

## Tests

```bash
uv run pytest apps/ -v
```

Nécessite une base PostgreSQL réelle (pas de SQLite) : la contrainte
d'exclusion GiST anti-chevauchement et les triggers d'audit n'existent que
sur PostgreSQL. `pytest-django` crée/détruit une base de test dédiée à
chaque run (l'utilisateur configuré doit avoir le droit `CREATEDB`).

## Flux métier principal

1. `POST /api/v2/auth/login/ {email, mot_de_passe}` → `access` + `refresh` (JWT).
2. `POST /api/v2/creneaux/` (gestionnaire) → crée un créneau `DISPONIBLE` sur une salle.
3. `POST /api/v2/reservations/ {creneau}` (membre) → réservation `EN_ATTENTE`
   (acompte = durée × tarif horaire de la salle), créneau passé `RESERVE`.
4. `POST /api/v2/paiements/ {reservation, montant, moyen}` (membre) → déclenche
   le mock de paiement. Accepté → événement `PaiementValide` → la réservation
   passe automatiquement `CONFIRMEE` (revalidation anti-chevauchement contre
   les réservations déjà `CONFIRMEE`, avec la contrainte GIST EXCLUDE en base
   comme filet de sécurité ultime). Refusé → événement `PaiementEchoue` → la
   réservation est libérée (`ANNULEE`, créneau repassé `DISPONIBLE`).
5. `PATCH /api/v2/reservations/{id}/` (membre propriétaire, uniquement si
   `CONFIRMEE`) → annulation (cancel-and-release : le créneau redevient
   `DISPONIBLE`).

Les événements `PaiementValide`/`PaiementEchoue` sont propagés en
in-process (synchrone) via `apps.core.domain.dispatcher`, câblé dans
`apps/core/apps.py::ready()` — remplaçable par un vrai bus de messages sans
changer les Domain Events ni les use cases.

## KPIs (gestionnaire uniquement)

- `GET /api/v2/kpis/occupation/?debut=YYYY-MM-DD&fin=YYYY-MM-DD`
- `GET /api/v2/kpis/revenu/?debut=YYYY-MM-DD&fin=YYYY-MM-DD`
- `GET /api/v2/kpis/dashboard/?debut=YYYY-MM-DD&fin=YYYY-MM-DD`

## Audit

Toute écriture sur `reservation`/`paiement` est journalisée automatiquement
(table append-only `audit_log`, index BRIN sur `horodatage`) par un trigger
PL/pgSQL qui lit l'acteur et l'IP positionnés en session par
`apps.core.middleware.AuditContextMiddleware` à chaque requête.

## Ce qui reste volontairement simulé

- `apps/paiements` : passerelle de paiement mock (`MockPaymentGateway`,
  toujours acceptée par défaut) — aucune intégration bancaire réelle.
- La documentation conceptuelle CH2 (architecture "une base par
  microservice") décrit la cible logique ; l'implémentation réelle de ce
  dépôt utilise une base PostgreSQL unique partagée, comme demandé.
