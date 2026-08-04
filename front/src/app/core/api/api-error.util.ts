import { AxiosError } from 'axios';
import { ApiError } from '../models';

type DrfErrorBody = string | string[] | Record<string, string | string[]>;

function flattenFieldErrors(body: Record<string, string | string[]>): Record<string, string[]> {
  const fieldErrors: Record<string, string[]> = {};
  for (const [field, value] of Object.entries(body)) {
    fieldErrors[field] = Array.isArray(value) ? value : [value];
  }
  return fieldErrors;
}

function extractMessage(body: DrfErrorBody): string {
  if (typeof body === 'string') {
    return body;
  }
  if (Array.isArray(body)) {
    return body.join(' ');
  }
  if ('detail' in body && typeof body['detail'] === 'string') {
    return body['detail'];
  }
  const firstValue = Object.values(body)[0];
  if (Array.isArray(firstValue)) {
    return firstValue[0] ?? 'Une erreur est survenue.';
  }
  return typeof firstValue === 'string' ? firstValue : 'Une erreur est survenue.';
}

export function normalizeApiError(error: unknown): ApiError {
  if (isAxiosError(error)) {
    const status = error.response?.status ?? 0;
    const data = error.response?.data;

    if (status === 0) {
      return { status, message: 'Impossible de contacter le serveur.', fieldErrors: {} };
    }
    if (!data) {
      return { status, message: error.message || 'Une erreur est survenue.', fieldErrors: {} };
    }

    const body = data as DrfErrorBody;
    const fieldErrors =
      typeof body === 'object' && !Array.isArray(body) ? flattenFieldErrors(body as Record<string, string | string[]>) : {};
    return { status, message: extractMessage(body), fieldErrors };
  }
  return { status: 0, message: 'Une erreur inattendue est survenue.', fieldErrors: {} };
}

function isAxiosError(error: unknown): error is AxiosError {
  return typeof error === 'object' && error !== null && 'isAxiosError' in error;
}
