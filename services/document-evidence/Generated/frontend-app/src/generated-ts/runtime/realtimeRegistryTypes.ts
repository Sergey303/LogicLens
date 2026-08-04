
import type {
  RealtimeCommandDescriptorMap,
  RealtimeEnvelope,
  RealtimeEventDescriptorMap,
  RealtimeEventHandlers,
} from "./realtimeTypes";

export interface RealtimeRegistry<
  TEventPayloadByKey extends object,
  TCommandPayloadByKey extends object,
  TCommandAckByKey extends object,
  TEventsByKey extends RealtimeEventDescriptorMap = RealtimeEventDescriptorMap,
  TCommandsByKey extends RealtimeCommandDescriptorMap = RealtimeCommandDescriptorMap,
> {
  readonly eventsByKey: TEventsByKey;
  readonly commandsByKey: TCommandsByKey;
  readonly descriptorsByKey: Readonly<TEventsByKey & TCommandsByKey>;
  readonly endpointKeysByRealtimeLink: Readonly<Record<string, readonly string[]>>;
  readonly endpointKeysByInvalidatedByRealtimeEventKey: Readonly<Record<string, readonly string[]>>;
  readonly getEventDescriptor: <K extends Extract<keyof TEventsByKey, string>>(realtimeKey: K) => TEventsByKey[K] | undefined;
  readonly getCommandDescriptor: <K extends Extract<keyof TCommandsByKey, string>>(realtimeKey: K) => TCommandsByKey[K] | undefined;
  readonly getRelatedEndpointKeys: <K extends Extract<keyof TEventPayloadByKey | keyof TCommandPayloadByKey, string>>(
    realtimeKey: K,
  ) => readonly string[];
  readonly resolveAffectedEndpointKeys: <K extends Extract<keyof TEventPayloadByKey | keyof TCommandPayloadByKey, string>>(
    realtimeKey: K,
  ) => readonly string[];
  readonly createEnvelope: <K extends Extract<keyof TEventPayloadByKey, string>>(
    realtimeKey: K,
    payload: TEventPayloadByKey[K],
  ) => RealtimeEnvelope<K, TEventPayloadByKey[K]>;
  readonly dispatchEvent: <K extends Extract<keyof TEventPayloadByKey, string>>(
    handlers: RealtimeEventHandlers<TEventPayloadByKey>,
    envelope: RealtimeEnvelope<K, TEventPayloadByKey[K]>,
  ) => boolean;
}
