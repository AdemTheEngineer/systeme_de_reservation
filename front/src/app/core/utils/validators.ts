import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

const TELEPHONE_TN_PATTERN = /^\+216\d{8}$/;
const PASSWORD_MIN_LENGTH = 8;

export function telephoneTunisienValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value as string | null;
    if (!value) {
      return null;
    }
    return TELEPHONE_TN_PATTERN.test(value) ? null : { telephoneInvalide: true };
  };
}

export function motDePasseFortValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = control.value as string | null;
    if (!value) {
      return null;
    }
    const errors: ValidationErrors = {};
    if (value.length < PASSWORD_MIN_LENGTH) {
      errors['tropCourt'] = true;
    }
    if (!/[A-Z]/.test(value)) {
      errors['sansMajuscule'] = true;
    }
    if (!/[0-9]/.test(value)) {
      errors['sansChiffre'] = true;
    }
    return Object.keys(errors).length > 0 ? errors : null;
  };
}

export function motsDePasseIdentiquesValidator(passwordKey: string, confirmationKey: string): ValidatorFn {
  return (group: AbstractControl): ValidationErrors | null => {
    const password = group.get(passwordKey)?.value as string | null;
    const confirmation = group.get(confirmationKey)?.value as string | null;
    if (!password || !confirmation) {
      return null;
    }
    return password === confirmation ? null : { motsDePasseDifferents: true };
  };
}
