import { useCallback, useRef, useState } from "react";
import type { OperationLifecycle, OperationStatus, OperationProgress, OperationAvailability } from "./operationLifecycleTypes";
import { createLinkedAbortController } from "./abortRuntime";

export interface OperationBinding<TInput, TOutput> {
  readonly execute: (input: TInput, options?: { signal?: AbortSignal; onProgress?: (event: unknown) => void }) => {
    readonly promise: Promise<TOutput>;
    readonly cancel: () => void;
  };
  readonly getAvailability: () => OperationAvailability;
}

export function useOperationLifecycle<TInput, TOutput, TError = unknown>(
  binding: OperationBinding<TInput, TOutput>,
  normalizeInput: (input: unknown) => TInput,
): OperationLifecycle<TOutput, TError> {
  const [status, setStatus] = useState<OperationStatus>("idle");
  const [error, setError] = useState<TError | null>(null);
  const [result, setResult] = useState<TOutput | null>(null);
  const [progress, setProgress] = useState<OperationProgress | null>(null);
  const abortRef = useRef<{ cancel: () => void } | null>(null);
  const lastInputRef = useRef<readonly unknown[] | null>(null);
  const runIdRef = useRef(0);
  const availability = binding.getAvailability();

  const cancel = useCallback(() => {
    abortRef.current?.cancel();
    abortRef.current = null;
    runIdRef.current += 1;
    setStatus("idle");
  }, []);

  const run = useCallback(
    async (...args: readonly unknown[]): Promise<TOutput> => {
      abortRef.current?.cancel();
      const runId = ++runIdRef.current;
      setStatus("running");
      setError(null);
      setProgress(null);

      const abort = createLinkedAbortController();
      abortRef.current = abort;

      lastInputRef.current = args;

      const input = normalizeInput(args[0]);
      const execution = binding.execute(input, {
        signal: abort.signal,
        onProgress: (event: unknown) => {
          const ev = event as { kind?: string; loaded?: number; total?: number | null; lengthComputable?: boolean };
          if (ev && typeof ev.loaded === "number") {
            setProgress({
              phase: ev.kind === "upload" ? "upload" : "download",
              loadedBytes: ev.loaded,
              totalBytes: ev.total ?? null,
              percent: ev.lengthComputable && ev.total ? Math.round((ev.loaded / ev.total) * 100) : null,
            });
          }
        },
      });

      try {
        const data = await execution.promise;
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
    [binding, normalizeInput],
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

