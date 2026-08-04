# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django/DRF backend for a private coworking-space reservation system, built with
Domain-Driven Design. The core bounded context (`reservations`) has the full
4-layer DDD structure; support contexts (`identite`, `paiements`) are lighter
(direct Django models, no tactical DDD). All contexts share a single PostgreSQL
database (`systeme_reservation_db`); cross-context FKs are allowed (e.g.
`Reservation.membre` → `identite.Membre`).

Code, comments, docstrings, and domain terms are in **French** — keep new code
consistent with this (e.g. `Salle`, `Creneau`, `Montant`, `EN_ATTENTE`).

## Commands

Package manager is `uv` exclusively — no `pip` anywhere in this project.

```bash
uv sync                                    # install dependencies
uv run python manage.py runserver          # dev server → http://localhost:8000/api/v2/
uv run python manage.py migrate
uv run python manage.py makemigrations reservations   # ⚠ see MIGRATION_MODULES note below
uv run pytest apps/ -v                     # full test suite
uv run pytest apps/reservations/tests/domain/test_entities.py -v   # single file
uv run pytest apps/reservations/tests -k test_confirmer_reservation -v  # single test
```

Tests **require a real PostgreSQL database** (not SQLite): the anti-overlap
GiST exclusion constraint (needs the `btree_gist` extension, enabled by
`infrastructure/migrations/0002_reservation_no_overlap_exclusion.py`) and the
audit triggers only exist on Postgres. `pytest-django` creates/destroys a
dedicated test database per run — the configured DB user needs `CREATEDB`.
Config lives in `pyproject.toml` (`DJANGO_SETTINGS_MODULE`,
`testpaths = ["apps"]`, `addopts = "--reuse-db"` — the test DB persists
between runs, so after editing migrations run with `--create-db` once to
force a rebuild).

Docker Compose (`docker compose up --build`) runs Postgres 16 + the backend,
auto-applies migrations, then starts `runserver` on port 8000.

Env vars are read from `.env` (copy from `.env.example`) via `django-environ`:
`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_*`, `JWT_ACCESS_MINUTES`,
`JWT_REFRESH_DAYS`.

## Architecture

### API surface

All routes are mounted under `/api/v2/`, assembled in `config/urls.py` by
including each context's own `interfaces/api/urls.py` (no central route
list — check the three files if you need the full picture):

- `apps/identite` — `auth/login/`, `auth/refresh/`, `auth/logout/`, `auth/me/`,
  plus DRF-router `membres/` and `gestionnaires/` viewsets.
- `apps/reservations` — DRF-router `salles/`, `creneaux/`, `reservations/`
  viewsets, plus plain views `salles/disponibles/` and the KPI endpoints
  `kpis/occupation/`, `kpis/revenu/`, `kpis/dashboard/` (gestionnaire-only;
  use cases in `application/use_cases/kpis.py`).
- `apps/paiements` — DRF-router `paiements/` viewset only.

### Layering in `apps/reservations` (the core context)

- `domain/` — pure Python, **zero Django dependency**. `entities.py` holds the
  Aggregate Root `Reservation` plus `Salle`/`Paiement` entities; all mutation
  goes through Aggregate methods (`Reservation.creer/confirmer/annuler/liberer`),
  never direct attribute writes. `value_objects.py` has immutable VOs
  (`Creneau`, `Montant`). `repositories.py` defines abstract repository
  interfaces (ports). `services.py` holds domain services. `events.py` defines
  Domain Events as frozen dataclasses. `exceptions.py` holds domain invariant
  violations (`ChevauchementCreneauError`, `TransitionInvalideError`, etc.).
- `application/` — use cases (commands/queries) orchestrate domain +
  repositories + event publishing; no business rules here, no Django ORM
  calls directly (only through repository ports). `dto.py` holds
  input/output DTOs. `exceptions.py` holds "not found" / orchestration errors,
  distinct from domain exceptions.
- `infrastructure/` — Django ORM models (`models.py`), concrete repository
  implementations (`repositories.py`) fulfilling the domain ports, and
  `mappers.py` translating between Entities and ORM models (the *only* place
  this translation happens — no Entity ever subclasses `models.Model`).
- `interfaces/api/` — DRF viewsets/views: parse request → call use case →
  serialize response → map exceptions to HTTP codes. No business logic.
  `views.py::reservation_exception_handler` (wired via
  `REST_FRAMEWORK.EXCEPTION_HANDLER` in settings) maps domain/application
  exceptions to 404/409/400.

`apps/identite` and `apps/paiements` skip the `domain/application/infrastructure`
split — they use direct Django models (`models.py`) and lighter `services.py`/
`gateway.py`, since they're support contexts, not the core domain.

`apps/core` is the **Shared Kernel**: `domain/base_entity.py` (`Entity`,
identity-based equality), `domain/base_value_object.py` (`ValueObject`),
`domain/domain_event.py` (`DomainEvent` base), and `domain/dispatcher.py` (the
in-process event dispatcher singleton). All pure Python, no Django dependency.

### Migrations location quirk

`apps/reservations` keeps its migrations in `infrastructure/migrations/`
instead of the Django-default `apps/reservations/migrations/`, wired via
`MIGRATION_MODULES` in `config/settings.py`. Keep this in mind when running
`makemigrations`/`migrate` for that app, or when looking for its migration
files. `identite`, `paiements`, `core` use the default location.

### Cross-context event flow (the main business flow)

Contexts never call each other directly — they communicate through Domain
Events and the in-process dispatcher (`apps.core.domain.dispatcher`). The
*only* place contexts are wired together is the composition root
`apps/core/apps.py::CoreConfig.ready()`. The dispatcher's contract
(`register`/`dispatch`) is designed to be swappable for a real message broker
later without touching the events or use cases.

Flow: `POST /reservations/` creates a reservation `EN_ATTENTE` (acompte =
duration × room hourly rate) and marks its `CreneauSlot` `RESERVE`. A separate
`POST /paiements/` call (`InitierPaiementUseCase`) runs the mock payment
gateway (`apps/paiements/gateway.py::MockPaymentGateway` — always accepts by
default, no real bank integration) and dispatches `PaiementValide` or
`PaiementEchoue` (`apps/paiements/domain/events.py`) via
`transaction.on_commit`. Those events are handled in `CoreConfig.ready()`:
- `PaiementValide` → `ConfirmerReservationUseCase` → `EN_ATTENTE` → `CONFIRMEE`
  (re-checks overlap against already-`CONFIRMEE` reservations, since
  `EN_ATTENTE` doesn't block booking at creation time — see the long docstring
  in `domain/entities.py::Reservation.confirmer` for why).
- `PaiementEchoue` → `LibererCreneauUseCase` → reservation `ANNULEE`, slot back
  to `DISPONIBLE` (cancel-and-release).

The Postgres GiST `EXCLUDE` constraint on `reservation` (scoped to
`statut='CONFIRMEE'`, added in `infrastructure/migrations/0002_...py`) is the
last-resort safety net against a genuine race between concurrent
confirmations — the application-level overlap check is the primary guard.

`confirmer_reservation`/`liberer_creneau` use cases are **not** exposed via any
HTTP route — they only fire from the event handlers above.

### Audit logging

Every write to `reservation`/`paiement` is journaled automatically by a
PL/pgSQL trigger (`audit_log_trigger`, generic via `TG_ARGV[0]` for the PK
column name) into an append-only `audit_log` table (BRIN index on
`horodatage`) — see `apps/core/migrations/0002_audit_triggers.py`. The
trigger reads actor/IP from `current_setting('app.current_user_id'/'app.client_ip')`,
set per-request by `apps/core/middleware.py::AuditContextMiddleware`. That
middleware resolves the user via JWT directly (not `request.user`) because
DRF/SimpleJWT authentication hasn't run yet at the middleware stage, and uses
`set_config(..., is_local=false)` (session-scoped) because autocommit mode
means a plain `SET LOCAL` wouldn't survive across the ORM's per-statement
mini-transactions.

### Auth & permissions

`apps.identite.Utilisateur` is `AUTH_USER_MODEL`, login by `email` (no
`username`), via JWT (`djangorestframework-simplejwt`). `Membre` and
`Gestionnaire` are two profile models (`OneToOneField` to `Utilisateur`).
Permission classes (`interfaces/api/permissions.py`) are pure authorization,
never business rules: `EstProprietaireDeLaReservation` (object-level, owner
only), `EstGestionnaireOuLectureSeule` (read = any authenticated user, write =
gestionnaire only).

### Reservation vs CreneauSlot

`Creneau` (domain Value Object: date + heure_debut/heure_fin, with
`.chevauche()` overlap check) is distinct from `CreneauSlot` (infrastructure
model: a bookable catalog resource with a `DISPONIBLE`/`RESERVE` status,
what `POST /reservations/ {creneau_id}` actually references). Don't conflate
the two when reading `reserver_creneau.py` or the repositories.

### Testing pattern

`apps/reservations/tests/` mirrors the layer structure (`domain/`,
`application/`, `infrastructure/`, `api/`). Application-layer tests use
in-memory fakes (`tests/application/fakes.py`) implementing the repository
ports instead of hitting the database — only `infrastructure/` and `api/`
tests need real Postgres.
