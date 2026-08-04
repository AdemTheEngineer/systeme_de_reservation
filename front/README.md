# Système de Réservation d'Espaces de Coworking — Frontend

Application Angular (standalone, signals, zoneless) pour le système de
réservation d'espaces de coworking. Ce frontend consomme l'API REST du
backend Django/DRF (voir `../systeme_de_reservation_backend`).

## Stack technique

- **Angular 22** — composants standalone uniquement, signals (`signal`,
  `computed`, `effect`, `input()`, `output()`, `model()`), nouveau control
  flow (`@if`/`@for`/`@switch`/`@defer`), zoneless
  (`provideZonelessChangeDetection`).
- **TypeScript strict** — `strict: true`, `noUncheckedIndexedAccess`,
  `noUnusedLocals`, etc. Aucun `any`.
- **axios** — seul client HTTP, encapsulé dans `core/api/api.service.ts`
  (jamais appelé directement depuis un composant).
- **Tailwind CSS v4** — seule feuille de style autorisée : `src/styles.css`
  (import Tailwind + jetons de thème `@theme`). Aucun CSS de composant.
- **Formulaires réactifs** (`ReactiveFormsModule`, `FormGroup` typés) —
  aucun formulaire piloté par template, aucun `ngModel`.
- **`@lucide/angular`** — pour les icônes uniquement.

## Prérequis

- Node.js 20+ et npm.
- Le backend Django doit tourner en local sur `http://localhost:8000`
  (voir `../systeme_de_reservation_backend/CLAUDE.md` pour son
  installation — en résumé : `uv sync`, un PostgreSQL local avec la base
  `systeme_reservation_db`, puis `uv run python manage.py migrate`).

## Installation

```bash
npm install
```

## Lancer l'application en développement

```bash
npm start          # équivalent à `ng serve --port 4200`
```

Ouvrir <http://localhost:4200>.

**Important — proxy de développement.** Le backend Django n'expose aucun
en-tête CORS (aucun `django-cors-headers` n'est configuré côté backend, et ce
frontend n'a pas vocation à modifier le code Python). `ng serve` doit donc
être utilisé (pas un simple serveur de fichiers statiques après `ng build`) :
`proxy.conf.json` redirige toutes les requêtes `/api/*` vers
`http://localhost:8000`, ce qui rend les appels same-origin du point de vue
du navigateur. Ce proxy est déjà déclaré dans `angular.json`
(`projects.front.architect.serve.options.proxyConfig`).

## Variables d'environnement

Pas de fichier `.env` — la configuration se fait via les fichiers
TypeScript `src/environments/` (remplacés au build par
`fileReplacements` dans `angular.json`) :

| Fichier | Utilisé pour | `apiBaseUrl` |
|---|---|---|
| `environment.ts` | `ng serve` (développement) | `/api/v2` (relatif, via le proxy) |
| `environment.prod.ts` | `ng build` (production) | `/api/v2` (à adapter selon la passerelle Nginx du déploiement) |

## Build de production

```bash
npm run build
```

Sortie dans `dist/front/`. Le build échoue sur toute erreur TypeScript ou
de template — `npx tsc --noEmit` peut être lancé séparément pour un
contrôle de types isolé.

## Comptes de démonstration

Le backend est fourni avec des données de seed
(`apps/identite/management/commands/seed_identite.py`). Tout utilisateur
`*.seed@example.com` fonctionne, avec le mot de passe commun
`Coworking#2026` (sauf si l'administrateur backend l'a changé au moment du
seed).

## Carte des routes par rôle

L'application est **entièrement privée** : toute route hors `/auth/**` est
protégée par `authGuard` (utilisateur connecté) et, pour les espaces
`/membre/**` et `/gestionnaire/**`, par `roleGuard` (rôle correspondant).
Un utilisateur du mauvais rôle est redirigé vers `/403`.

| Route | Accès | Écran |
|---|---|---|
| `/auth/login` | Public | Connexion |
| `/403` | Public | Accès refusé |
| `/**` (inconnue) | Public | Page introuvable (404) |
| `/dev/ui` | Public | Vitrine du système de design (`shared/ui/*`) |
| `/membre` | Membre | Tableau de bord (statistiques de réservation) |
| `/membre/espaces` | Membre | Catalogue des espaces (filtres, recherche) |
| `/membre/espaces/:id` | Membre | Détail d'un espace + créneaux disponibles |
| `/membre/reservations` | Membre | Mes réservations (onglets de statut, annulation) |
| `/membre/reservations/nouvelle?creneau=:id` | Membre | Assistant de réservation (créneau → récapitulatif → paiement) |
| `/membre/profil` | Membre | Profil (lecture seule — voir note ci-dessous) |
| `/gestionnaire` | Gestionnaire | Tableau de bord (KPIs, graphiques SVG) |
| `/gestionnaire/espaces` | Gestionnaire | Gestion des espaces (CRUD, activation/désactivation) |
| `/gestionnaire/espaces/:id/creneaux` | Gestionnaire | Gestion des créneaux d'un espace |
| `/gestionnaire/reservations` | Gestionnaire | Toutes les réservations (filtres, détail) |
| `/gestionnaire/paiements` | Gestionnaire | Paiements (statuts, pagination) |
| `/gestionnaire/membres` | Gestionnaire | Membres (liste, création) |
| `/gestionnaire/profil` | Gestionnaire | Profil (lecture seule) |

## Écarts assumés avec le brief initial

Le backend réel diverge sur plusieurs points structurants d'une hypothèse de
brief plus générique (API à 3 microservices, inscription publique, créneaux
libres). Les adaptations retenues sont documentées dans le code aux points
concernés, et récapitulées ici :

1. **Pas d'inscription publique.** `POST /membres/` exige un compte
   gestionnaire authentifié. La création de membres se fait donc depuis
   *Gestionnaire → Membres*, pas depuis une page publique.
2. **Réservation par créneau, pas par horaire libre.** Un membre choisit un
   créneau existant (`Creneau`, géré par les gestionnaires) plutôt que de
   saisir une heure de début/fin arbitraire.
3. **Profil en lecture seule.** `GET /auth/me/` n'expose pas l'identifiant
   `Membre`/`Gestionnaire` nécessaire pour appeler les endpoints de mise à
   jour, et `MembreViewSet` est de toute façon réservé aux gestionnaires.
4. **Filtres du catalogue.** Seuls la recherche par nom et le filtre de
   capacité minimale sont côté serveur ; le type d'espace, la ville
   (dérivée du champ libre `localisation`) et la fourchette de tarif sont
   filtrés côté client, faute de support serveur.

## Structure du projet

```
src/app/
  core/       api (axios), auth (store + guards), models, services, utils
  shared/     ui/ (bibliothèque de composants), layout/ (AppShell, Sidebar…), pipes/
  layout/     coquilles de route par rôle (MembreShell, GestionnaireShell)
  features/   écrans, organisés par domaine (auth, espaces, reservations, …)
  dev-ui/     vitrine du système de design (/dev/ui)
```
