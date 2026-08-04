import { useCallback, useRef, useState } from "react";
import type { OperationLifecycle, OperationStatus, OperationProgress, OperationAvailability } from "./operationLifecycleTypes";

/**
 * Mutation-specific lifecycle that wraps mutateAsync instead of binding.execute.
 * This preserves the TanStack React Query mutation pipeline:
 * - mutation.mutateAsync(input) triggers onSuccess, onError, onSettled
 * - generated invalidateEndpointKeys runs via options.onSuccess
 * - TanStack mutation state (isPending, isSuccess, etc.) stays consistent
 *
 * The lifecycle exposes the same OperationLifecycle interface so generated hooks
 * can consume it uniformly, but run() goes through mutateAsync rather than
 * bypassing it.
 */
export function useMutationLifecycle<TInput, TOutput, TError = unknown>(
  mutateAsync: (input: TInput) => Promise<TOutput>,
  normalizeInput: (input: unknown) => TInput,
  getAvailability: () => OperationAvailability,
): OperationLifecycle<TOutput, TError> {
  const [status, setStatus] = useState<OperationStatus>("idle");
  const [error, setError] = useState<TError | null>(null);
  const [result, setResult] = useState<TOutput | null>(null);
  const [progress, setProgress] = useState<OperationProgress | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const lastInputRef = useRef<readonly unknown[] | null>(null);
  const runIdRef = useRef(0);
  const availability = getAvailability();

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    runIdRef.current += 1;
    setStatus("idle");
  }, []);

  const run = useCallback(
    async (...args: readonly unknown[]): Promise<TOutput> => {
      abortRef.current?.abort();
      const runId = ++runIdRef.current;
      setStatus("running");
      setError(null);
      setProgress(null);

      const controller = new AbortController();
      abortRef.current = controller;

      lastInputRef.current = args;

      const input = normalizeInput(args[0]);

      try {
        const data = await mutateAsync(input);
        if (runId !== runIdRef.current) {
          return data;
        }
        setResult(data);
        setStatus("success");
        abortRef.current = null;
        return data;
      } catch (err) {
        if (runId !== runIdRef.current) {
          throw err;
        }
        const typedError = err as TError;
        setError(typedError);
        setStatus("error");
        abortRef.current = null;
        throw typedError;
      }
    },
    [mutateAsync, normalizeInput],
  );

  const retry = useCallback((): Promise<TOutput> => {
    if (lastInputRef.current) {
      return run(...lastInputRef.current);
    }
    throw new Error("retry unavailable before first run");
  }, [run]);

  return {
    run,
    cancel,
    retry,
    status,
    isRunning: status === "running",
    error,
    result,
    progress,
    availability,
  };
}
