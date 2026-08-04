export interface ReconnectOptions {
  readonly maxAttempts?: number;
  readonly baseDelayMs?: number;
  readonly maxDelayMs?: number;
  readonly onReconnect?: (attempt: number) => void;
}

export interface ReconnectManager {
  readonly start: () => void;
  readonly stop: () => void;
  readonly reset: () => void;
  readonly isRunning: boolean;
}

export function createReconnectManager(
  connect: () => void,
  options?: ReconnectOptions,
): ReconnectManager {
  const maxAttempts = options?.maxAttempts ?? Infinity;
  const baseDelayMs = options?.baseDelayMs ?? 1000;
  const maxDelayMs = options?.maxDelayMs ?? 30000;
  let attempt = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let running = false;

  function schedule(): void {
    if (!running || timer !== null || attempt >= maxAttempts) {
      return;
    }

    const delay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
    const jitter = delay * (0.5 + Math.random() * 0.5);

    timer = setTimeout(() => {
      timer = null;
      if (!running || attempt >= maxAttempts) {
        return;
      }
      attempt++;
      options?.onReconnect?.(attempt);
      connect();
    }, jitter);
  }

  function start(): void {
    running = true;
    schedule();
  }

  function stop(): void {
    running = false;
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function reset(): void {
    attempt = 0;
    stop();
  }

  return {
    start,
    stop,
    reset,
    get isRunning(): boolean {
      return running;
    },
  };
}
