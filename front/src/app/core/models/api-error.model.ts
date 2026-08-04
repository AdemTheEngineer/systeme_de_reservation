export interface ApiError {
  status: number;
  message: string;
  fieldErrors: Record<string, string[]>;
}
