import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { MutationFunctionContext } from "@tanstack/react-query";
import type { ActionBinding } from "./actionRuntime";
import { invalidateEndpointKeys } from "./reactInvalidation";
import { normalizeEndpointInput } from "./reactEndpointInput";
import { useMutationLifecycle } from "./mutationLifecycleRuntime";
import { useOperationLifecycle } from "./operationLifecycleRuntime";
import type { MutationBinding } from "./mutationRuntime";
import type { QueryKey } from "./queryKeyRuntime";
import type { QueryBinding } from "./queryRuntime";
import type {
  GeneratedActionHookResult,
  GeneratedActionOptions,
  GeneratedEndpointInput,
  GeneratedMutationHookResult,
  GeneratedMutationOptions,
  GeneratedQueryHookResult,
  GeneratedQueryOptions,
} from "./reactQueryTypes";
import type { TransportResponseMetadata } from "./responseMetadata";

export { invalidateEndpointKeys };
export { useGeneratedStream } from "./reactStreamRuntime";

export function useGeneratedQuery<TInput, TOutput, TError = unknown>(
  binding: QueryBinding<TInput, TOutput>,
  input: GeneratedEndpointInput<TInput>,
  options?: GeneratedQueryOptions<TOutput, TError>,
): GeneratedQueryHookResult<TInput, TOutput, TError> {
  const availability = binding.getAvailability();
  const normalizedInput = normalizeEndpointInput(input) as TInput;
  const enabled = (options?.enabled ?? true) && availability.isVisible && availability.isEnabled;
  const query = useQuery<TOutput, TError, TOutput, QueryKey>({
    ...options,
    queryKey: binding.getQueryKey(normalizedInput),
    queryFn: ({ signal }: { signal?: AbortSignal }) => binding.execute(normalizedInput, { signal }).promise,
    enabled,
  });

  const lifecycle = useOperationLifecycle<TInput, TOutput, TError>(
    binding as unknown as Parameters<typeof useOperationLifecycle<TInput, TOutput, TError>>[0],
    (raw: unknown) => normalizeEndpointInput(raw) as TInput,
  );

  return {
    ...query,
    binding,
    availability,
    isVisible: availability.isVisible,
    isEnabled: availability.isEnabled,
    disabledReason: availability.disabledReason,
    query,
    execute: (nextInput: GeneratedEndpointInput<TInput>) =>
      binding.execute(normalizeEndpointInput(nextInput) as TInput).promise,
    lifecycle,
  };
}

export function useGeneratedMutation<TInput, TOutput, TError = unknown, TContext = unknown>(
  binding: MutationBinding<TInput, TOutput>,
  options?: GeneratedMutationOptions<TInput, TOutput, TError, TContext>,
): GeneratedMutationHookResult<TInput, TOutput, TError, TContext> {
  const queryClient = useQueryClient();
  const availability = binding.getAvailability();
  const lastResponseRef = useRef<TransportResponseMetadata | null>(null);
  const affectedEndpointKeys = binding.getAffectedEndpointKeys();
  const shouldHandleSuccess = options?.onSuccess !== undefined
    || (options?.invalidateOnSuccess !== false && affectedEndpointKeys.length > 0);
  const onSuccess = shouldHandleSuccess
    ? async (
        data: TOutput,
        variables: GeneratedEndpointInput<TInput>,
        context: TContext,
        mutationFunctionContext: MutationFunctionContext,
      ) => {
        await options?.onSuccess?.(data, variables, context, mutationFunctionContext);
        if (options?.invalidateOnSuccess !== false && affectedEndpointKeys.length > 0) {
          await invalidateEndpointKeys(queryClient, affectedEndpointKeys);
        }
      }
    : undefined;
  const mutation = useMutation<TOutput, TError, GeneratedEndpointInput<TInput>, TContext>({
    ...options,
    mutationFn: (input: GeneratedEndpointInput<TInput>) =>
      binding.execute(normalizeEndpointInput(input) as TInput, {
        onResponse: (metadata) => {
          lastResponseRef.current = metadata;
          options?.onResponse?.(metadata);
        },
      }).promise,
    onSuccess,
  });

  const lifecycle = useMutationLifecycle<TInput, TOutput, TError>(
    (input: TInput) => mutation.mutateAsync(normalizeEndpointInput(input) as GeneratedEndpointInput<TInput>),
    (raw: unknown) => normalizeEndpointInput(raw) as TInput,
    () => binding.getAvailability(),
  );

  return {
    ...mutation,
    binding,
    availability,
    isVisible: availability.isVisible,
    isEnabled: availability.isEnabled,
    disabledReason: availability.disabledReason,
    mutation,
    execute: (input: GeneratedEndpointInput<TInput>) =>
      mutation.mutateAsync(input),
    lifecycle,
    lastResponse: lastResponseRef.current,
    warnings: lastResponseRef.current?.warnings ?? [],
  };
}

export function useGeneratedAction<TInput, TOutput, TError = unknown, TContext = unknown>(
  binding: ActionBinding<TInput, TOutput>,
  options?: GeneratedActionOptions<TInput, TOutput, TError, TContext>,
): GeneratedActionHookResult<TInput, TOutput, TError, TContext> {
  const result = useGeneratedMutation<TInput, TOutput, TError, TContext>(binding, options);
  return {
    ...result,
    binding,
    action: result.mutation,
    redirect: (input?: GeneratedEndpointInput<TInput>) => {
      result.mutation.mutate(input as GeneratedEndpointInput<TInput>);
    },
  };
}
