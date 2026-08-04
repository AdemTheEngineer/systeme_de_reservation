import { Component, OnInit, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiError, Membre } from '../../../core/models';
import { MembresService } from '../../../core/services/membres.service';
import { motDePasseFortValidator, telephoneTunisienValidator } from '../../../core/utils/validators';
import { DateFrPipe } from '../../../shared/pipes/date-fr.pipe';
import { Button } from '../../../shared/ui/button/button';
import { Card } from '../../../shared/ui/card/card';
import { Drawer } from '../../../shared/ui/drawer/drawer';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';
import { Icon } from '../../../shared/ui/icon/icon';
import { Input } from '../../../shared/ui/input/input';
import { PageHeader } from '../../../shared/layout/page-header/page-header';
import { Modal } from '../../../shared/ui/modal/modal';
import { Pagination } from '../../../shared/ui/pagination/pagination';
import { Skeleton } from '../../../shared/ui/skeleton/skeleton';
import { Table } from '../../../shared/ui/table/table';
import { ToastService } from '../../../shared/ui/toast/toast.service';

interface MembreFormGroup {
  email: FormControl<string>;
  telephone: FormControl<string>;
  mot_de_passe: FormControl<string>;
}

const PAGE_SIZE = 20;

@Component({
  selector: 'app-membres-admin-liste',
  imports: [ReactiveFormsModule, Button, Card, Drawer, EmptyState, Icon, Input, Modal, PageHeader, Pagination, Skeleton, Table, DateFrPipe],
  template: `
    <app-page-header title="Membres" description="Consultez et créez les comptes membres.">
      <ui-button variant="primary" (click)="openCreate()">
        <ui-icon name="plus" [size]="16" />
        Nouveau membre
      </ui-button>
    </app-page-header>

    <ui-card [padded]="false">
      <div class="p-4">
        <ui-input placeholder="Rechercher par e-mail…" [formControl]="searchControl" />
      </div>

      @if (loading()) {
        <div class="flex flex-col gap-2 p-4 pt-0">
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
          <ui-skeleton widthClass="w-full" heightClass="h-10" />
        </div>
      } @else if (membres().length === 0) {
        <ui-empty-state icon="users" title="Aucun membre" description="Aucun membre ne correspond à cette recherche." />
      } @else {
        <div class="hidden md:block">
          <ui-table>
            <thead class="bg-neutral-50 text-xs uppercase text-neutral-500">
              <tr>
                <th class="px-4 py-2.5 font-medium">E-mail</th>
                <th class="px-4 py-2.5 font-medium">Téléphone</th>
                <th class="px-4 py-2.5 font-medium">Inscrit le</th>
              </tr>
            </thead>
            <tbody>
              @for (m of membres(); track m.id) {
                <tr class="cursor-pointer border-t border-neutral-200 hover:bg-neutral-50" (click)="selected.set(m)">
                  <td class="px-4 py-3 font-medium text-neutral-900">{{ m.email }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ m.telephone || '—' }}</td>
                  <td class="px-4 py-3 text-neutral-600">{{ m.date_creation | dateFr: 'date' }}</td>
                </tr>
              }
            </tbody>
          </ui-table>
        </div>

        <div class="flex flex-col gap-3 p-4 pt-0 md:hidden">
          @for (m of membres(); track m.id) {
            <div class="cursor-pointer rounded-lg border border-neutral-200 p-3" (click)="selected.set(m)">
              <p class="font-medium text-neutral-900">{{ m.email }}</p>
              <p class="text-sm text-neutral-500">{{ m.telephone || '—' }} · Inscrit le {{ m.date_creation | dateFr: 'date' }}</p>
            </div>
          }
        </div>

        <div class="p-4">
          <ui-pagination [count]="count()" [pageSize]="pageSize" [page]="page()" (pageChange)="onPageChange($event)" />
        </div>
      }
    </ui-card>

    <ui-drawer [open]="!!selected()" title="Détail du membre" (closed)="selected.set(null)">
      @if (selected(); as m) {
        <dl class="flex flex-col gap-4">
          <div>
            <dt class="text-xs uppercase text-neutral-500">E-mail</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ m.email }}</dd>
          </div>
          <div>
            <dt class="text-xs uppercase text-neutral-500">Téléphone</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ m.telephone || '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs uppercase text-neutral-500">Inscrit le</dt>
            <dd class="text-sm font-medium text-neutral-900">{{ m.date_creation | dateFr: 'datetime' }}</dd>
          </div>
        </dl>
      }
    </ui-drawer>

    <ui-modal [open]="modalOpen()" title="Nouveau membre" (closed)="modalOpen.set(false)">
      <form [formGroup]="form" (ngSubmit)="submit()" class="flex flex-col gap-4">
        <ui-input label="Adresse e-mail" type="email" [required]="true" [formControl]="form.controls.email" />
        <ui-input label="Téléphone" placeholder="+21620123456" [formControl]="form.controls.telephone" hint="Format : +216 suivi de 8 chiffres." />
        <ui-input label="Mot de passe" type="password" [required]="true" [formControl]="form.controls.mot_de_passe" hint="8 caractères minimum, avec une majuscule et un chiffre." />

        @if (formError()) {
          <p class="text-sm text-rose-600" role="alert">{{ formError() }}</p>
        }

        <div class="mt-2 flex justify-end gap-3">
          <ui-button type="button" variant="secondary" (click)="modalOpen.set(false)">Annuler</ui-button>
          <ui-button type="submit" variant="primary" [loading]="submitting()" [disabled]="form.invalid">Créer le membre</ui-button>
        </div>
      </form>
    </ui-modal>
  `,
})
export class MembresAdminListe implements OnInit {
  private readonly membresService = inject(MembresService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toastService = inject(ToastService);

  protected readonly pageSize = PAGE_SIZE;
  protected readonly searchControl = new FormControl('', { nonNullable: true });

  protected readonly loading = signal(true);
  protected readonly membres = signal<Membre[]>([]);
  protected readonly count = signal(0);
  protected readonly page = signal(1);
  protected readonly selected = signal<Membre | null>(null);

  protected readonly modalOpen = signal(false);
  protected readonly submitting = signal(false);
  protected readonly formError = signal('');

  protected readonly form = new FormGroup<MembreFormGroup>({
    email: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
    telephone: new FormControl('', { nonNullable: true, validators: [telephoneTunisienValidator()] }),
    mot_de_passe: new FormControl('', { nonNullable: true, validators: [Validators.required, motDePasseFortValidator()] }),
  });

  async ngOnInit(): Promise<void> {
    const initial = this.route.snapshot.queryParamMap;
    this.searchControl.setValue(initial.get('q') ?? '', { emitEvent: false });
    this.page.set(Number(initial.get('page') ?? 1));

    this.searchControl.valueChanges.subscribe(() => {
      this.page.set(1);
      this.syncAndLoad();
    });

    await this.loadMembres();
  }

  protected openCreate(): void {
    this.form.reset({ email: '', telephone: '', mot_de_passe: '' });
    this.formError.set('');
    this.modalOpen.set(true);
  }

  protected onPageChange(page: number): void {
    this.page.set(page);
    this.syncAndLoad();
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.formError.set('');
    try {
      await this.membresService.create(this.form.getRawValue());
      this.toastService.success('Membre créé avec succès.');
      this.modalOpen.set(false);
      await this.loadMembres();
    } catch (error) {
      this.formError.set((error as ApiError).message);
    } finally {
      this.submitting.set(false);
    }
  }

  private syncAndLoad(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { q: this.searchControl.value || null, page: this.page() },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    void this.loadMembres();
  }

  private async loadMembres(): Promise<void> {
    this.loading.set(true);
    try {
      const result = await this.membresService.list({ search: this.searchControl.value || undefined, page: this.page() });
      this.membres.set(result.results);
      this.count.set(result.count);
    } finally {
      this.loading.set(false);
    }
  }
}
