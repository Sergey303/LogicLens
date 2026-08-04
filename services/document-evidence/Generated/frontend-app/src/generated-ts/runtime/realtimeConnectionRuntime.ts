import type { RealtimeConnectionLifecycle, RealtimeConnectionState, RealtimeConnectionStatus } from "./realtimeConnectionTypes";
import { createReconnectManager } from "./realtimeReconnectRuntime";
import type { ReconnectOptions } from "./realtimeReconnectRuntime";

export interface RealtimeConnectionOptions {
  readonly url: string;
  readonly onOpen?: () => void;
  readonly onMessage?: (data: unknown) => void;
  readonly onClose?: (event: { code: number; reason: string }) => void;
  readonly onError?: (error: Event) => void;
  readonly reconnect?: ReconnectOptions;
}

export function createRealtimeConnectionLifecycle(
  options: RealtimeConnectionOptions,
): RealtimeConnectionLifecycle {
  let ws: WebSocket | null = null;
  let status: RealtimeConnectionStatus = "disconnected";
  let lastConnectedAt: number | null = null;
  let lastDisconnectedAt: number | null = null;
  let lastError: Error | null = null;
  let reconnectAttempt = 0;
  const listeners = new Set<(state: RealtimeConnectionState) => void>();

  const reconnectManager = createReconnectManager(
    () => {
      reconnectAttempt++;
      setStatus("reconnecting");
      connect();
    },
    {
      ...options.reconnect,
      onReconnect: (attempt: number) => {
        options.reconnect?.onReconnect?.(attempt);
      },
    },
  );

  function emitState(): void {
    const state: RealtimeConnectionState = {
      status,
      lastConnectedAt,
      lastDisconnectedAt,
      lastError,
      reconnectAttempt,
      isConnected: status === "connected",
    };
    for (const listener of listeners) {
      listener(state);
    }
  }

  function setStatus(newStatus: RealtimeConnectionStatus): void {
    status = newStatus;
    emitState();
  }

  function connect(): void {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setStatus("connecting");

    try {
      ws = new WebSocket(options.url);

      ws.onopen = () => {
        lastConnectedAt = Date.now();
        lastDisconnectedAt = null;
        lastError = null;
        reconnectAttempt = 0;
        reconnectManager.reset();
        setStatus("connected");
        options.onOpen?.();
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data) as unknown;
          options.onMessage?.(parsed);
        } catch {
          options.onMessage?.(event.data);
        }
      };

      ws.onclose = (event: CloseEvent) => {
        lastDisconnectedAt = Date.now();
        ws = null;
        setStatus("disconnected");
        options.onClose?.({ code: event.code, reason: event.reason });
        reconnectManager.start();
      };

      ws.onerror = (event: Event) => {
        lastError = new Error("WebSocket error");
        setStatus("error");
        options.onError?.(event);
        reconnectManager.start();
      };
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      setStatus("error");
    }
  }

  function disconnect(): void {
    reconnectManager.stop();
    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    lastDisconnectedAt = Date.now();
    setStatus("disconnected");
  }

  function retry(): void {
    reconnectManager.stop();
    disconnect();
    reconnectAttempt++;
    setStatus("reconnecting");
    connect();
  }

  function subscribe(listener: (state: RealtimeConnectionState) => void): () => void {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }

  return {
    get state(): RealtimeConnectionState {
      return { status, lastConnectedAt, lastDisconnectedAt, lastError, reconnectAttempt, isConnected: status === "connected" };
    },
    connect,
    disconnect,
    retry,
    subscribe,
  };
}
