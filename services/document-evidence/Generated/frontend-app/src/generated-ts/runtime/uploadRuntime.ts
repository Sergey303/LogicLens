export interface TransferProgress {
  phase: "upload" | "download";
  loadedBytes: number;
  totalBytes: number | null;
  percent: number | null;
}

export interface ProgressOperationHandle<T> {
  promise: Promise<T>;
  cancel: () => void;
  subscribeProgress: (listener: (progress: TransferProgress) => void) => () => void;
}

