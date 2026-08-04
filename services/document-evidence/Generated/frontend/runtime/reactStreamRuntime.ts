import { useCallback, useEffect, useRef, useState } from "react";
import { normalizeEndpointInput } from "./reactEndpointInput";
import type { QueryBinding, QueryExecution } from "./queryRuntime";
import type {
  GeneratedEndpointInput,
  GeneratedStreamHookResult,
  GeneratedStreamOptions,
} from "./reactQueryTypes";

export function useGeneratedStream<TInput, TItem, TError = unknown>(
  binding: QueryBinding<TInput, AsyncIterable<TItem>>,
  input: GeneratedEndpointInput<TInput>,
  options?: GeneratedStreamOptions<TItem, TError>,
): GeneratedStreamHookResult<TInput, TItem, TError> {
  const availability = binding.getAvailability();
  const [items, setItems] = useState<readonly TItem[]>([]);
  const [latestItem, setLatestItem] = useState<TItem | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<TError | null>(null);
  const executionRef = useRef<QueryExecution<AsyncIterable<TItem>> | null>(null);

  const cancel = useCallback(() => {
    executionRef.current?.cancel();
    executionRef.current = null;
    setIsStreaming(false);
  }, []);

  const clear = useCallback(() => {
    setItems([]);
    setLatestItem(null);
    setError(null);
  }, []);

  const start = useCallback(async (nextInput?: GeneratedEndpointInput<TInput>): Promise<readonly TItem[]> => {
    if (!availability.isVisible || !availability.isEnabled) {
      return [];
    }

    executionRef.current?.cancel();
    const normalizedInput = normalizeEndpointInput(nextInput === undefined ? input : nextInput) as TInput;
    const execution = binding.execute(normalizedInput);
    executionRef.current = execution;
    const collected: TItem[] = [];

    setItems([]);
    setLatestItem(null);
    setError(null);
    setIsStreaming(true);

    try {
      const stream = await execution.promise;
      for await (const item of stream) {
        collected.push(item);
        setLatestItem(item);
        setItems((previous) => [...previous, item]);
        options?.onItem?.(item);
      }
      options?.onComplete?.(collected);
      return collected;
    } catch (caught) {
      const typedError = caught as TError;
      setError(typedError);
      options?.onError?.(typedError);
      throw typedError;
    } finally {
      if (executionRef.current === execution) {
        executionRef.current = null;
        setIsStreaming(false);
      }
    }
  }, [availability.isEnabled, availability.isVisible, binding, input, options]);

  useEffect(() => {
    const enabled = (options?.enabled ?? true)
      && (options?.autoStart ?? true)
      && availability.isVisible
      && availability.isEnabled;
    if (!enabled) {
      return undefined;
    }

    void start(input);
    return cancel;
  }, [availability.isEnabled, availability.isVisible, cancel, input, options?.autoStart, options?.enabled, start]);

  return {
    binding,
    availability,
    isVisible: availability.isVisible,
    isEnabled: availability.isEnabled,
    disabledReason: availability.disabledReason,
    items,
    latestItem,
    isStreaming,
    error,
    start,
    cancel,
    clear,
  };
}
