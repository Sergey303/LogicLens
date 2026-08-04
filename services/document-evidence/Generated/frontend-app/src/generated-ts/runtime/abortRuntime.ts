export interface LinkedAbortController {
  readonly signal: AbortSignal;
  readonly cancel: () => void;
}

/**
 * Creates a local AbortController and optionally links it to an external signal.
 * The returned cancel() always aborts the local signal, while an external abort
 * also aborts the local signal.
 */
export function createLinkedAbortController(externalSignal?: AbortSignal): LinkedAbortController {
  const controller = new AbortController();

  if (externalSignal?.aborted) {
    controller.abort(externalSignal.reason);
  } else if (externalSignal) {
    externalSignal.addEventListener(
      "abort",
      () => controller.abort(externalSignal.reason),
      { once: true },
    );
  }

  return {
    signal: controller.signal,
    cancel: () => controller.abort(),
  };
}
