/**
 * Reusable form helpers wrapping react-hook-form.
 *
 * The goal of this module is to keep the boilerplate around form submission
 * identical across the app so we can change behaviour (e.g. add telemetry
 * or a different toast pattern) in one place.
 *
 * Conventions:
 *  - All forms use zod schemas via ``@hookform/resolvers/zod``.
 *  - The server-side error envelope (see backend/app/core/error_handler.py)
 *    is unwrapped here so callers don't need to re-implement the parsing
 *    in every form.
 */
import { useCallback, useState } from 'react';
import { useForm, type UseFormProps, type FieldValues, type Path, type Resolver } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { getErrorDetails } from './errorMessages';
import toast from 'react-hot-toast';

/**
 * Build a typed react-hook-form instance with any zod schema whose parsed
 * output is an object (i.e. a ``FieldValues``-compatible shape).
 *
 * Note: we type the schema as ``object`` (non-structural) to avoid the
 * zod v4 / @hookform/resolvers generic variance issue; callers express the
 * concrete type through the optional ``TForm`` parameter to ``useZodForm``
 * or rely on inference from ``defaultValues``.
 */
export function useZodForm<TForm extends FieldValues>(
  schema: object,
  options?: Omit<UseFormProps<TForm>, 'resolver'>,
) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const resolver = zodResolver(schema as any) as Resolver<TForm, any>;
  return useForm<TForm>({
    resolver,
    ...options,
  });
}

/**
 * Wrap a react-hook-form submit handler with consistent UX:
 *  - Parse server-side errors with ``getErrorDetails``.
 *  - Show a toast for non-validation errors (network, server, etc.).
 *  - Show a success toast on completion.
 *  - Track an ``isSubmitting`` state.
 *
 * The wrapped handler accepts the same arguments as ``handleSubmit`` and
 * returns ``Promise<void>`` — never rejects. Validation errors stay on the
 * form via react-hook-form's normal ``formState.errors`` mechanism.
 */
export function useFormSubmit<T extends FieldValues>(
  handleSubmit: ReturnType<typeof useForm<T>>['handleSubmit'],
  doSubmit: (data: T) => Promise<unknown> | unknown,
  options?: {
    success?: string;
    onSuccess?: (data: T) => void;
    onError?: (error: unknown) => void;
  },
) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submit = useCallback(
    (e?: React.BaseSyntheticEvent) =>
      handleSubmit(async (data) => {
        setIsSubmitting(true);
        try {
          await doSubmit(data);
          if (options?.success) toast.success(options.success);
          options?.onSuccess?.(data);
        } catch (error) {
          const details = getErrorDetails(error);
          // Only toast non-validation errors (those stay on the form).
          const status = (error as any)?.response?.status;
          if (status !== 400 && status !== 422) {
            toast.error(`${details.title}: ${details.message}`);
          }
          options?.onError?.(error);
        } finally {
          setIsSubmitting(false);
        }
      })(e),
    [handleSubmit, doSubmit, options],
  );

  return { submit, isSubmitting };
}

/**
 * Set a field-level server error on a react-hook-form instance.
 *
 * Backend Pydantic validation errors come back as
 * ``[{loc: ['body', 'field_name'], msg: 'must be greater than 0'}]``.
 * This helper projects them onto the form so the field shows the message.
 */
export function applyServerErrors<T extends FieldValues>(
  setError: ReturnType<typeof useForm<T>>['setError'],
  error: unknown,
  fieldMap: Record<string, Path<T>> = {},
) {
  const details = error as any;
  const serverErrors = details?.response?.data?.details;
  if (!Array.isArray(serverErrors)) return;
  for (const err of serverErrors) {
    const path: string[] | undefined = err?.loc;
    if (!path || path.length === 0) continue;
    const last = String(path[path.length - 1]);
    const field = fieldMap[last] ?? (last as Path<T>);
    if (err?.msg) setError(field, { type: 'server', message: String(err.msg) });
  }
}
