export type Ok<T> = { success: true; data: T };
export type Err<E> = { success: false; error: E };
export type Result<T> = Ok<T> | Err<string>;
