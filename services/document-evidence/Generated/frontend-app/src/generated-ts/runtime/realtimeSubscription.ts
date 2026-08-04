
import type { RealtimeSubscription, RealtimeSubscriptionOptions } from "./realtimeTypes";

export function combineRealtimeSubscriptions(
  ...subscriptions: ReadonlyArray<RealtimeSubscription | null | undefined>
): RealtimeSubscription {
  return createRealtimeSubscription(() => {
    for (const subscription of subscriptions) {
      subscription?.unsubscribe();
    }
  });
}

export function createRealtimeSubscription(unsubscribe: () => void): RealtimeSubscription;
export function createRealtimeSubscription(
  eventKeys: readonly string[],
  options?: RealtimeSubscriptionOptions,
): RealtimeSubscription;
export function createRealtimeSubscription(
  arg1: (() => void) | readonly string[],
  options: RealtimeSubscriptionOptions = {},
): RealtimeSubscription {
  if (typeof arg1 === "function") {
    return { unsubscribe: arg1 };
  }

  console.warn(`[realtimeRuntime] Created no-op subscription for event keys: ${arg1.join(", ")}.`);
  void options;

  return {
    unsubscribe: () => {
      // No-op
    },
  };
}

export function isRealtimeEventKeyMatch(eventKey: string, subscribedKeys: readonly string[]): boolean {
  return subscribedKeys.includes(eventKey);
}
