// ------------------------------------------------------------------------------
// GENERATED FILE - source: shared/realtime.generated.ts
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { defineRealtimeRegistry } from "../runtime/realtimeRuntime";
import { endpointKeysByInvalidatedByRealtimeEventKey } from "./contracts/realtime/endpointKeysByInvalidatedByRealtimeEventKey.generated";
import { endpointKeysByRealtimeLink } from "./contracts/realtime/endpointKeysByRealtimeLink.generated";
import { sharedRealtimeCommandsByKey } from "./realtime/commands.generated";
import { sharedRealtimeEventsByKey } from "./realtime/events.generated";
import type { SharedRealtimeCommandAckByKey, SharedRealtimeCommandPayloadByKey, SharedRealtimeEventPayloadByKey } from "./realtime/payloads.generated";

export const sharedRealtimeDescriptorsByKey = {
  ...sharedRealtimeEventsByKey,
  ...sharedRealtimeCommandsByKey,
} as const;

export type SharedRealtimeEventKey = keyof typeof sharedRealtimeEventsByKey;
export type SharedRealtimeCommandKey = keyof typeof sharedRealtimeCommandsByKey;
export type SharedRealtimeKey = keyof typeof sharedRealtimeDescriptorsByKey;

export const sharedRealtimeRegistry = defineRealtimeRegistry<
  SharedRealtimeEventPayloadByKey,
  SharedRealtimeCommandPayloadByKey,
  SharedRealtimeCommandAckByKey
>({
  eventsByKey: sharedRealtimeEventsByKey,
  commandsByKey: sharedRealtimeCommandsByKey,
  endpointKeysByRealtimeLink,
  endpointKeysByInvalidatedByRealtimeEventKey,
});
