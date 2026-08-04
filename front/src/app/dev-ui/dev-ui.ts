import { Component, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Avatar } from '../shared/ui/avatar/avatar';
import { Badge, BadgeTone } from '../shared/ui/badge/badge';
import { Button } from '../shared/ui/button/button';
import { Card } from '../shared/ui/card/card';
import { ConfirmDialog } from '../shared/ui/confirm-dialog/confirm-dialog';
import { DatePicker } from '../shared/ui/date-picker/date-picker';
import { Drawer } from '../shared/ui/drawer/drawer';
import { EmptyState } from '../shared/ui/empty-state/empty-state';
import { Icon } from '../shared/ui/icon/icon';
import { Input } from '../shared/ui/input/input';
import { Modal } from '../shared/ui/modal/modal';
import { Pagination } from '../shared/ui/pagination/pagination';
import { Select, SelectOption } from '../shared/ui/select/select';
import { Skeleton } from '../shared/ui/skeleton/skeleton';
import { StatCard } from '../shared/ui/stat-card/stat-card';
import { Table } from '../shared/ui/table/table';
import { Tabs, TabItem } from '../shared/ui/tabs/tabs';
import { Textarea } from '../shared/ui/textarea/textarea';
import { ToastContainer } from '../shared/ui/toast/toast-container';
import { ToastService } from '../shared/ui/toast/toast.service';
import { Tooltip } from '../shared/ui/tooltip/tooltip';

const BADGE_TONES: { tone: BadgeTone; label: string }[] = [
  { tone: 'success', label: 'Confirmée' },
  { tone: 'warning', label: 'En attente' },
  { tone: 'danger', label: 'Annulée' },
  { tone: 'neutral', label: 'Réservé' },
  { tone: 'info', label: 'Info' },
];

const VILLE_OPTIONS: SelectOption[] = [
  { value: 'tunis', label: 'Tunis' },
  { value: 'sousse', label: 'Sousse' },
  { value: 'sfax', label: 'Sfax' },
];

const CATALOGUE_TABS: TabItem[] = [
  { value: 'tous', label: 'Tous' },
  { value: 'confirmees', label: 'Confirmées' },
  { value: 'attente', label: 'En attente' },
];

@Component({
  selector: 'app-dev-ui',
  imports: [
    ReactiveFormsModule,
    Avatar,
    Badge,
    Button,
    Card,
    ConfirmDialog,
    DatePicker,
    Drawer,
    EmptyState,
    Icon,
    Input,
    Modal,
    Pagination,
    Select,
    Skeleton,
    StatCard,
    Table,
    Tabs,
    Textarea,
    ToastContainer,
    Tooltip,
  ],
  template: `
    <div class="mx-auto flex max-w-5xl flex-col gap-8 p-6 sm:p-10">
      <header class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold text-neutral-900">Vitrine du système de design</h1>
        <p class="text-sm text-neutral-500">
          Vérification visuelle de la règle 60&nbsp;% blanc / 30&nbsp;% noir &amp; gris / 10&nbsp;% accent.
        </p>
      </header>

      <ui-card>
        <h2 class="mb-4 text-lg font-semibold text-neutral-900">Boutons</h2>
        <div class="flex flex-wrap items-center gap-3">
          <ui-button variant="primary">Primaire</ui-button>
          <ui-button variant="secondary">Secondaire</ui-button>
          <ui-button variant="ghost">Discret</ui-button>
          <ui-button variant="danger">Destructif</ui-button>
          <ui-button variant="primary" [loading]="true">Chargement</ui-button>
          <ui-button variant="primary" [disabled]="true">Désactivé</ui-button>
        </div>
      </ui-card>

      <ui-card>
        <h2 class="mb-4 text-lg font-semibold text-neutral-900">Champs de formulaire</h2>
        <div class="grid gap-4 sm:grid-cols-2">
          <ui-input label="Nom de l'espace" placeholder="Ex. Open Space Lac 1" [formControl]="nomControl" />
          <ui-select label="Ville" placeholder="Choisir une ville" [options]="villeOptions" [formControl]="villeControl" />
          <ui-date-picker label="Date" kind="date" [formControl]="dateControl" />
          <ui-date-picker label="Heure" kind="time" [formControl]="heureControl" />
          <div class="sm:col-span-2">
            <ui-textarea label="Description" placeholder="Décrire l'espace…" [formControl]="descriptionControl" />
          </div>
          <ui-input label="Champ en erreur" [formControl]="erreurControl" errorMessage="Ce champ est obligatoire." />
        </div>
      </ui-card>

      <ui-card>
        <h2 class="mb-4 text-lg font-semibold text-neutral-900">Badges de statut</h2>
        <div class="flex flex-wrap gap-2">
          @for (item of badgeTones; track item.tone) {
            <ui-badge [tone]="item.tone">{{ item.label }}</ui-badge>
          }
        </div>
      </ui-card>

      <div class="grid gap-4 sm:grid-cols-3">
        <ui-stat-card label="Réservations à venir" value="3" icon="calendar-days" />
        <ui-stat-card label="Heures réservées ce mois" value="24h" icon="clock" hint="+4h vs. mois dernier" />
        <ui-stat-card label="Montant dépensé" value="360,000 TND" icon="wallet" />
      </div>

      <ui-card>
        <h2 class="mb-4 text-lg font-semibold text-neutral-900">Onglets</h2>
        <ui-tabs [tabs]="catalogueTabs" [(active)]="activeTab" />
      </ui-card>

      <ui-card [padded]="false">
        <h2 class="p-4 pb-0 text-lg font-semibold text-neutral-900">Tableau</h2>
        <div class="p-4">
          <ui-table>
            <thead class="bg-neutral-50 text-xs uppercase text-neutral-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">Espace</th>
                <th class="px-4 py-2.5 font-medium">Date</th>
                <th class="px-4 py-2.5 font-medium">Statut</th>
                <th class="px-4 py-2.5 font-medium">Montant</th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-t border-neutral-200 hover:bg-neutral-50">
                <td class="px-4 py-3 text-neutral-900">Salle Carthage</td>
                <td class="px-4 py-3 text-neutral-600">04/08/2026</td>
                <td class="px-4 py-3"><ui-badge tone="success">Confirmée</ui-badge></td>
                <td class="px-4 py-3 text-neutral-900">45,000 TND</td>
              </tr>
              <tr class="border-t border-neutral-200 hover:bg-neutral-50">
                <td class="px-4 py-3 text-neutral-900">Open Space Lac</td>
                <td class="px-4 py-3 text-neutral-600">05/08/2026</td>
                <td class="px-4 py-3"><ui-badge tone="warning">En attente</ui-badge></td>
                <td class="px-4 py-3 text-neutral-900">20,000 TND</td>
              </tr>
            </tbody>
          </ui-table>
        </div>
        <div class="p-4 pt-0">
          <ui-pagination [count]="42" [pageSize]="10" [(page)]="page" />
        </div>
      </ui-card>

      <ui-card>
        <h2 class="mb-4 text-lg font-semibold text-neutral-900">Superpositions</h2>
        <div class="flex flex-wrap items-center gap-3">
          <ui-button variant="secondary" (click)="modalOpen.set(true)">Ouvrir une modale</ui-button>
          <ui-button variant="secondary" (click)="drawerOpen.set(true)">Ouvrir un tiroir</ui-button>
          <ui-button variant="danger" (click)="confirmOpen.set(true)">Dialogue de confirmation</ui-button>
          <ui-button variant="secondary" (click)="toasts.success('Réservation confirmée avec succès.')">
            Notification succès
          </ui-button>
          <ui-button variant="secondary" (click)="toasts.error('Ce créneau n\\'est plus disponible.')">
            Notification erreur
          </ui-button>
        </div>
      </ui-card>

      <ui-card>
        <h2 class="mb-4 text-lg font-semibold text-neutral-900">Avatars, infobulle &amp; squelettes</h2>
        <div class="flex flex-wrap items-center gap-4">
          <ui-avatar name="Amine Ben Salah" size="sm" />
          <ui-avatar name="Amine Ben Salah" size="md" />
          <ui-avatar name="Amine Ben Salah" size="lg" />
          <ui-tooltip text="Espace disponible dès 08:00">
            <ui-icon name="info" [size]="18" />
          </ui-tooltip>
          <div class="flex flex-1 flex-col gap-2">
            <ui-skeleton widthClass="w-1/3" heightClass="h-4" />
            <ui-skeleton widthClass="w-full" heightClass="h-4" />
          </div>
        </div>
      </ui-card>

      <ui-card>
        <h2 class="mb-4 text-lg font-semibold text-neutral-900">État vide</h2>
        <ui-empty-state icon="calendar-days" title="Aucune réservation" description="Vous n'avez pas encore réservé d'espace de coworking.">
          <ui-button variant="primary">Découvrir les espaces</ui-button>
        </ui-empty-state>
      </ui-card>
    </div>

    <ui-modal [open]="modalOpen()" title="Exemple de modale" (closed)="modalOpen.set(false)">
      <p class="text-sm text-neutral-600">Contenu de la modale, avec piège de focus et fermeture via Échap.</p>
    </ui-modal>

    <ui-drawer [open]="drawerOpen()" title="Détail de la réservation" (closed)="drawerOpen.set(false)">
      <p class="text-sm text-neutral-600">Le tiroir glisse depuis la droite pour afficher un détail contextuel.</p>
    </ui-drawer>

    <ui-confirm-dialog
      [open]="confirmOpen()"
      title="Annuler la réservation ?"
      message="Cette action est définitive. Voulez-vous vraiment annuler cette réservation ?"
      confirmLabel="Annuler la réservation"
      [danger]="true"
      (cancelled)="confirmOpen.set(false)"
      (confirmed)="confirmOpen.set(false)"
    />

    <ui-toast-container />
  `,
})
export class DevUi {
  protected readonly badgeTones = BADGE_TONES;
  protected readonly villeOptions = VILLE_OPTIONS;
  protected readonly catalogueTabs = CATALOGUE_TABS;

  protected readonly nomControl = new FormControl('', { nonNullable: true });
  protected readonly villeControl = new FormControl('', { nonNullable: true });
  protected readonly dateControl = new FormControl('', { nonNullable: true });
  protected readonly heureControl = new FormControl('', { nonNullable: true });
  protected readonly descriptionControl = new FormControl('', { nonNullable: true });
  protected readonly erreurControl = new FormControl('', { nonNullable: true });

  protected readonly activeTab = signal('tous');
  protected readonly page = signal(1);
  protected readonly modalOpen = signal(false);
  protected readonly drawerOpen = signal(false);
  protected readonly confirmOpen = signal(false);

  protected readonly toasts = inject(ToastService);
}
