export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PageQuery {
  page?: number;
  search?: string;
  ordering?: string;
}
