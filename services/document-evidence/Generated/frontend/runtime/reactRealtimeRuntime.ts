import { useEffect, useRef, useSyncExternalStore } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { RealtimeConnectionLifecycle, RealtimeConnectionState } from "./realtimeConnectionTypes";
import type { RealtimeCommandRuntimeOptions } from "./realtimeCommandRuntime";
import type { RealtimeRegistry } from "./realtimeRegistryTypes";
import type { RealtimeEnvelope, RealtimeEventHandlers } from "./realtimeTypes";
import { dispatchRealtimeEnvelope } from "./realtimeHandlers";
import { invalidateEndpointKeys, invalidateResolvedEndpointKeys } from "./reactInvalidation";
import type { EndpointKeyResolver } from "./reactInvalidation";

export interface UseRealtimeConnectionResult {
  readonly state: RealtimeConnectionState;
  readonly connect: () => void;
  readonly disconnect: () => void;
  readonly retry: () => void;
}

export function useRealtimeConnection(
  lifecycle: RealtimeConnectionLifecycle,
): UseRealtimeConnectionResult {
  const state = useSyncExternalStore(
    lifecycle.subscribe,
    () => lifecycle.state,
    () => lifecycle.state,
  );

  return {
    state,
    connect: lifecycle.connect,
    disconnect: lifecycle.disconnect,
    retry: lifecycle.retry,
  };
}

export type RealtimeMessageSubscriber = (envelope: RealtimeEnvelope<string, unknown>) => void;

export function useRealtimeEventSubscription<
  TEventPayloadByKey extends object,
>(
  registry: RealtimeRegistry<TEventPayloadByKey, object, object>,
  handlers: RealtimeEventHandlers<TEventPayloadByKey>,
  subscribeToMessages: (handler: RealtimeMessageSubscriber) => () => void,
  enabled?: boolean,
): void {
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;
  const queryClient = useQueryClient();

  useEffect(() => {
    if (enabled === false) {
      return;
    }

    const eventKeys = Object.keys(handlers) as Extract<keyof TEventPayloadByKey, string>[];
    if (eventKeys.length === 0) {
      return;
    }

    const unsubscribe = subscribeToMessages((envelope: RealtimeEnvelope<string, unknown>) => {
      dispatchRealtimeEnvelope(
        handlersRef.current,
        envelope as RealtimeEnvelope<
          Extract<keyof TEventPayloadByKey, string>,
          TEventPayloadByKey[Extract<keyof TEventPayloadByKey, string>]
        >,
      );
      void invalidateResolvedEndpointKeys(queryClient, registry, envelope.realtimeKey);
    });

    return () => {
      unsubscribe();
    };
  }, [registry, queryClient, subscribeToMessages, enabled]);
}

export function useRealtimeInvalidationSubscription(
  registry: EndpointKeyResolver,
  subscribeToMessages: (handler: RealtimeMessageSubscriber) => () => void,
  enabled?: boolean,
): void {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (enabled === false) {
      return;
    }

    const unsubscribe = subscribeToMessages((envelope) => {
      void invalidateResolvedEndpointKeys(queryClient, registry, envelope.realtimeKey);
    });

    return () => {
      unsubscribe();
    };
  }, [queryClient, registry, subscribeToMessages, enabled]);
}

export function useRealtimeCommandInvalidationOptions(
  registry: EndpointKeyResolver,
): Pick<RealtimeCommandRuntimeOptions, "resolveAffectedEndpointKeys" | "onAffectedEndpointKeys"> {
  const queryClient = useQueryClient();

  return {
    resolveAffectedEndpointKeys: (commandKey) => registry.resolveAffectedEndpointKeys(commandKey),
    onAffectedEndpointKeys: async (_commandKey, endpointKeys) => {
      await invalidateEndpointKeys(queryClient, endpointKeys);
    },
  };
}

export function dispatchRealtimeEventToRegistry<
  TEventPayloadByKey extends object,
>(
  registry: RealtimeRegistry<TEventPayloadByKey, object, object>,
  envelope: RealtimeEnvelope<Extract<keyof TEventPayloadByKey, string>, TEventPayloadByKey[Extract<keyof TEventPayloadByKey, string>]>,
): boolean {
  return registry.dispatchEvent({} as RealtimeEventHandlers<TEventPayloadByKey>, envelope);
}
