
export type OperationStatus = "idle" | "running" | "success" | "error";

export interface OperationLifecycle<TResult, TError = unknown> {
  readonly run: (...args: readonly unknown[]) => Promise<TResult>;
  readonly cancel: () => void;
  readonly retry: (() => Promise<TResult>) | undefined;
  readonly status: OperationStatus;
  readonly isRunning: boolean;
  readonly error: TError | null;
  readonly result: TResult | null;
  readonly progress: OperationProgress | null;
  readonly availability: OperationAvailability;
}

export interface OperationProgress {
  readonly phase: "upload" | "download";
  readonly loadedBytes: number;
  readonly totalBytes: number | null;
  readonly percent: number | null;
}

export interface OperationAvailability {
  readonly isVisible: boolean;
  readonly isEnabled: boolean;
  readonly disabledReason: string | null;
}
