import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { EmptyState } from '../../../shared/ui/empty-state/empty-state';

@Component({
  selector: 'app-not-found',
  imports: [RouterLink, EmptyState],
  template: `
    <div class="flex min-h-dvh items-center justify-center bg-neutral-50 p-4">
      <ui-empty-state icon="triangle-alert" title="Page introuvable" description="La page que vous cherchez n'existe pas ou a été déplacée.">
        <a
          routerLink="/"
          class="inline-flex h-10 items-center justify-center rounded-lg border border-brand-blue bg-brand-blue px-4 text-sm font-medium text-white
                 hover:bg-brand-blue-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2"
        >
          Retour à l'accueil
        </a>
      </ui-empty-state>
    </div>
  `,
})
export class NotFound {}
