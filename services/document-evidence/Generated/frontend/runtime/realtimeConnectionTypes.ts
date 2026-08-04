
export type RealtimeConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting" | "error";

export interface RealtimeConnectionState {
  readonly status: RealtimeConnectionStatus;
  readonly lastConnectedAt: number | null;
  readonly lastDisconnectedAt: number | null;
  readonly lastError: Error | null;
  readonly reconnectAttempt: number;
  readonly isConnected: boolean;
}

export interface RealtimeConnectionLifecycle {
  readonly state: RealtimeConnectionState;
  readonly connect: () => void;
  readonly disconnect: () => void;
  readonly retry: () => void;
  readonly subscribe: (listener: (state: RealtimeConnectionState) => void) => () => void;
}
