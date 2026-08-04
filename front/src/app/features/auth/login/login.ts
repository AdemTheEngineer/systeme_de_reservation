import { Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { Role } from '../../../core/models';
import { AuthStore } from '../../../core/auth/auth-store';
import { AuthService } from '../../../core/services/auth.service';
import { Button } from '../../../shared/ui/button/button';
import { Card } from '../../../shared/ui/card/card';
import { Input } from '../../../shared/ui/input/input';

interface LoginForm {
  email: FormControl<string>;
  mot_de_passe: FormControl<string>;
}

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, Button, Card, Input],
  template: `
    <div class="flex min-h-dvh items-center justify-center bg-neutral-50 p-4">
      <ui-card>
        <div class="w-full max-w-sm">
          <div class="mb-6 flex flex-col gap-1 text-center">
            <h1 class="text-xl font-semibold text-neutral-900">Connexion</h1>
            <p class="text-sm text-neutral-500">Espaces de coworking — accès réservé aux membres et gestionnaires.</p>
          </div>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="flex flex-col gap-4">
            <ui-input
              label="Adresse e-mail"
              type="email"
              placeholder="prenom.nom@example.com"
              [required]="true"
              [formControl]="form.controls.email"
            />
            <ui-input
              label="Mot de passe"
              type="password"
              placeholder="••••••••"
              [required]="true"
              [formControl]="form.controls.mot_de_passe"
            />

            @if (formError()) {
              <p class="text-sm text-rose-600" role="alert">{{ formError() }}</p>
            }

            <ui-button type="submit" [fullWidth]="true" [loading]="submitting()" [disabled]="form.invalid">
              Se connecter
            </ui-button>
          </form>
        </div>
      </ui-card>
    </div>
  `,
})
export class Login {
  private readonly authService = inject(AuthService);
  private readonly authStore = inject(AuthStore);
  private readonly router = inject(Router);

  protected readonly form = new FormGroup<LoginForm>({
    email: new FormControl('', { nonNullable: true, validators: [Validators.required, Validators.email] }),
    mot_de_passe: new FormControl('', { nonNullable: true, validators: [Validators.required] }),
  });

  protected readonly submitting = signal(false);
  protected readonly formError = signal('');

  protected async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    this.formError.set('');

    try {
      await this.authService.login(this.form.getRawValue());
      const role = this.authStore.role();
      await this.router.navigateByUrl(role === Role.Gestionnaire ? '/gestionnaire' : '/membre');
    } catch {
      this.formError.set('Adresse e-mail ou mot de passe incorrect.');
    } finally {
      this.submitting.set(false);
    }
  }
}
