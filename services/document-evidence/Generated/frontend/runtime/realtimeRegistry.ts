
import type { RealtimeRegistry } from "./realtimeRegistryTypes";
import type {
  RealtimeCommandDescriptorMap,
  RealtimeContractEntry,
  RealtimeEventDescriptorMap,
  RealtimeRegistryOptions,
} from "./realtimeTypes";
import { dispatchRealtimeEnvelope } from "./realtimeHandlers";

export function defineRealtimeRegistry<
  TEventPayloadByKey extends object,
  TCommandPayloadByKey extends object,
  TCommandAckByKey extends object,
  TEventsByKey extends RealtimeEventDescriptorMap = RealtimeEventDescriptorMap,
  TCommandsByKey extends RealtimeCommandDescriptorMap = RealtimeCommandDescriptorMap,
>(
  options: RealtimeRegistryOptions<TEventPayloadByKey, TCommandPayloadByKey, TCommandAckByKey, TEventsByKey, TCommandsByKey>,
): RealtimeRegistry<TEventPayloadByKey, TCommandPayloadByKey, TCommandAckByKey, TEventsByKey, TCommandsByKey> {
  const endpointKeysByRealtimeLink = options.endpointKeysByRealtimeLink ?? {};
  const endpointKeysByInvalidatedByRealtimeEventKey = options.endpointKeysByInvalidatedByRealtimeEventKey ?? {};
  const descriptorsByKey = { ...options.eventsByKey, ...options.commandsByKey } as Readonly<TEventsByKey & TCommandsByKey>;

  const getRelatedEndpointKeys = <K extends Extract<keyof TEventPayloadByKey | keyof TCommandPayloadByKey, string>>(
    realtimeKey: K,
  ): readonly string[] => {
    const descriptor = descriptorsByKey[realtimeKey as keyof typeof descriptorsByKey] as RealtimeContractEntry | undefined;
    return descriptor?.relatedEndpointKeys ?? [];
  };

  const resolveAffectedEndpointKeys = <K extends Extract<keyof TEventPayloadByKey | keyof TCommandPayloadByKey, string>>(
    realtimeKey: K,
  ): readonly string[] => {
    return collectAffectedEndpointKeys(
      realtimeKey,
      getRelatedEndpointKeys(realtimeKey),
      endpointKeysByRealtimeLink,
      endpointKeysByInvalidatedByRealtimeEventKey,
    );
  };

  return {
    eventsByKey: options.eventsByKey,
    commandsByKey: options.commandsByKey,
    descriptorsByKey,
    endpointKeysByRealtimeLink,
    endpointKeysByInvalidatedByRealtimeEventKey,
    getEventDescriptor: (realtimeKey) => options.eventsByKey[realtimeKey],
    getCommandDescriptor: (realtimeKey) => options.commandsByKey[realtimeKey],
    getRelatedEndpointKeys,
    resolveAffectedEndpointKeys,
    createEnvelope: (realtimeKey, payload) => ({ realtimeKey, payload }),
    dispatchEvent: (handlers, envelope) => dispatchRealtimeEnvelope(handlers, envelope),
  };
}

function collectAffectedEndpointKeys(
  realtimeKey: string,
  relatedEndpointKeys: readonly string[],
  endpointKeysByRealtimeLink: Readonly<Record<string, readonly string[]>>,
  endpointKeysByInvalidatedByRealtimeEventKey: Readonly<Record<string, readonly string[]>>,
): readonly string[] {
  const affected = new Set<string>();
  for (const endpointKey of relatedEndpointKeys) {
    affected.add(endpointKey);
  }
  for (const endpointKey of endpointKeysByRealtimeLink[realtimeKey] ?? []) {
    affected.add(endpointKey);
  }
  for (const endpointKey of endpointKeysByInvalidatedByRealtimeEventKey[realtimeKey] ?? []) {
    affected.add(endpointKey);
  }
  return Array.from(affected);
}
