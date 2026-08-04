
import type { RealtimeEnvelope, RealtimeEventHandlers } from "./realtimeTypes";

export function defineRealtimeHandlers<TEventPayloadByKey extends object>(
  handlers: RealtimeEventHandlers<TEventPayloadByKey>,
): RealtimeEventHandlers<TEventPayloadByKey> {
  return handlers;
}

export function dispatchRealtimeEnvelope<
  TEventPayloadByKey extends object,
  K extends Extract<keyof TEventPayloadByKey, string>,
>(
  handlers: RealtimeEventHandlers<TEventPayloadByKey>,
  envelope: RealtimeEnvelope<K, TEventPayloadByKey[K]>,
): boolean {
  const handler = handlers[envelope.realtimeKey] as ((event: RealtimeEnvelope<K, TEventPayloadByKey[K]>) => void) | undefined;
  if (!handler) {
    return false;
  }

  handler(envelope);
  return true;
}
