import type { Resolver, FieldErrors } from 'react-hook-form';
import type { ZodSchema, ZodIssue } from 'zod';

export function zodV4Resolver<T extends Record<string, unknown>>(schema: ZodSchema<T>): Resolver<T> {
  return async (values) => {
    const result = schema.safeParse(values);
    if (result.success) return { values: result.data as T, errors: {} };
    const issues: ZodIssue[] = (result.error as { issues?: ZodIssue[] }).issues ?? [];
    const errors: FieldErrors<T> = {};
    for (const issue of issues) {
      const path = issue.path.join('.') as keyof FieldErrors<T>;
      if (!errors[path]) (errors as Record<string, unknown>)[path as string] = { message: issue.message, type: issue.code };
    }
    return { values: {} as never, errors } as never;
  };
}
