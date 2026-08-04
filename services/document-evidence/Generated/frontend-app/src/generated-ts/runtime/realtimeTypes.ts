
export interface RealtimeSubscription {
  unsubscribe: () => void;
}

export interface RealtimeEvent<T = unknown> {
  eventKey: string;
  payload: T;
  timestamp: number;
}

export interface RealtimeSubscriptionOptions {
  onEvent?: (event: RealtimeEvent) => void;
  onError?: (error: Error) => void;
  onClose?: () => void;
}

export interface RealtimeContractEntry<TPayload = unknown, TAck = null> {
  readonly realtimeKey: string;
  readonly wireName: string;
  readonly payloadTypeRef: string | null;
  readonly ackTypeRef: string | null;
  readonly relatedEndpointKeys: readonly string[];
}

export interface RealtimeEventDescriptor<TPayload = unknown> extends RealtimeContractEntry<TPayload, null> {
  readonly direction: "event";
}

export interface RealtimeCommandDescriptor<TPayload = unknown, TAck = null> extends RealtimeContractEntry<TPayload, TAck> {
  readonly direction: "command";
}

export type RealtimeEventDescriptorMap = Readonly<Record<string, RealtimeEventDescriptor>>;
export type RealtimeCommandDescriptorMap = Readonly<Record<string, RealtimeCommandDescriptor>>;

export interface RealtimeEnvelope<TKey extends string = string, TPayload = unknown> {
  readonly realtimeKey: TKey;
  readonly payload: TPayload;
}

export type RealtimeEventHandlers<TEventPayloadByKey extends object> = Partial<{
  [K in Extract<keyof TEventPayloadByKey, string>]: (envelope: RealtimeEnvelope<K, TEventPayloadByKey[K]>) => void;
}>;

export interface RealtimeRegistryOptions<
  TEventPayloadByKey extends object,
  TCommandPayloadByKey extends object,
  TCommandAckByKey extends object,
  TEventsByKey extends RealtimeEventDescriptorMap = RealtimeEventDescriptorMap,
  TCommandsByKey extends RealtimeCommandDescriptorMap = RealtimeCommandDescriptorMap,
> {
  readonly eventsByKey: TEventsByKey;
  readonly commandsByKey: TCommandsByKey;
  readonly endpointKeysByRealtimeLink?: Readonly<Record<string, readonly string[]>>;
  readonly endpointKeysByInvalidatedByRealtimeEventKey?: Readonly<Record<string, readonly string[]>>;
}
