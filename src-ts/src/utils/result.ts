import { Err, Ok } from '@/types/result';

export function ok<T>(data: T): Ok<T> {
  return { success: true, data };
}

export function err(error: string): Err<string> {
  return { success: false, error };
}
