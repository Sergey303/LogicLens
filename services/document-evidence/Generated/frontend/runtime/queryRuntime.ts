import type { QueryKey } from "./queryKeyRuntime";
import { buildEndpointQueryKey } from "./queryKeyRuntime";
import { mapUnknownError } from "./errorRuntime";
import type { FrontendDomainError } from "./errorTypes";
import { resolveAvailability, resolveEndpointAvailability } from "./availabilityRuntime";
import type { AvailabilityDescriptor, AvailabilityState } from "./availabilityTypes";
import { sharedRealtimeRegistry } from "../shared/realtime.generated";
import { defineEndpointTransport } from "./transportRuntime";
import type { EndpointTransportBindingMetadata, TransportCallOptions } from "./transportTypes";
import { createLinkedAbortController } from "./abortRuntime";

export interface QueryBindingOptions<TInput, TOutput> {
  endpointKey: string;
  transportMetadata: EndpointTransportBindingMetadata;
  availability: AvailabilityDescriptor;
  errorRefs: readonly string[];
  realtimeLinks: readonly string[];
}

export interface QueryExecution<TOutput> {
  promise: Promise<TOutput>;
  cancel: () => void;
}

export interface QueryBinding<TInput, TOutput> {
  readonly endpointKey: string;
  readonly getAvailability: () => AvailabilityState;
  readonly getAvailabilityRefs: () => AvailabilityDescriptor;
  readonly getErrorRefs: () => readonly string[];
  readonly getQueryKey: (input: TInput) => QueryKey;
  readonly getLinkedRealtimeAffectedEndpointKeys: () => readonly string[];
  readonly shouldRefreshFromRealtime: (realtimeKey: string) => boolean;
  readonly getAffectedEndpointKeysForRealtime: (realtimeKey: string) => readonly string[];
  readonly execute: (input: TInput, options?: TransportCallOptions) => QueryExecution<TOutput>;
}

interface RealtimeRegistryLike {
  resolveAffectedEndpointKeys: (realtimeKey: string) => readonly string[];
}

const realtimeRegistry = sharedRealtimeRegistry as unknown as RealtimeRegistryLike;

export function defineQueryBinding<TInput, TOutput>(
  options: QueryBindingOptions<TInput, TOutput>,
): QueryBinding<TInput, TOutput> {
  const transport = defineEndpointTransport<TInput, TOutput>(options.transportMetadata);
  const linkedRealtimeAffectedEndpointKeys = resolveLinkedRealtimeAffectedEndpointKeys(options.realtimeLinks);

  const getQueryKey = (input: TInput): QueryKey => {
    return buildEndpointQueryKey(options.endpointKey, input);
  };

  return {
    endpointKey: options.endpointKey,
    getAvailability: () => resolveBindingAvailability(options.endpointKey, options.availability),
    getAvailabilityRefs: () => options.availability,
    getErrorRefs: () => options.errorRefs,
    getQueryKey,
    getLinkedRealtimeAffectedEndpointKeys: () => linkedRealtimeAffectedEndpointKeys,
    shouldRefreshFromRealtime: (realtimeKey) => {
      if (options.realtimeLinks.includes(realtimeKey)) {
        return true;
      }

      return realtimeRegistry.resolveAffectedEndpointKeys(realtimeKey).includes(options.endpointKey);
    },
    getAffectedEndpointKeysForRealtime: (realtimeKey) => {
      if (!options.realtimeLinks.includes(realtimeKey) && !realtimeRegistry.resolveAffectedEndpointKeys(realtimeKey).includes(options.endpointKey)) {
        return [];
      }

      return uniqueStrings([options.endpointKey, ...realtimeRegistry.resolveAffectedEndpointKeys(realtimeKey)]);
    },
    execute: (input: TInput, callOptions?: TransportCallOptions) => {
      const abort = createLinkedAbortController(callOptions?.signal);
      const transportOptions: TransportCallOptions = {
        ...callOptions,
        signal: abort.signal,
      };

      const promise = transport(input, transportOptions).catch((error) => {
        throw mapUnknownError(error, options.errorRefs) as FrontendDomainError;
      });

      return {
        promise,
        cancel: abort.cancel,
      };
    },
  };
}

function resolveBindingAvailability(endpointKey: string, descriptor: AvailabilityDescriptor): AvailabilityState {
  const endpointState = resolveEndpointAvailability(endpointKey);
  const descriptorState = resolveAvailability(descriptor);

  return {
    isVisible: endpointState.isVisible && descriptorState.isVisible,
    isEnabled: endpointState.isEnabled && descriptorState.isEnabled,
    disabledReason: endpointState.disabledReason ?? descriptorState.disabledReason,
  };
}

function resolveLinkedRealtimeAffectedEndpointKeys(realtimeLinks: readonly string[]): readonly string[] {
  const affected = new Set<string>();
  for (const realtimeKey of realtimeLinks) {
    for (const endpointKey of realtimeRegistry.resolveAffectedEndpointKeys(realtimeKey)) {
      affected.add(endpointKey);
    }
  }

  return Array.from(affected);
}

function uniqueStrings(values: readonly string[]): readonly string[] {
  return Array.from(new Set(values));
}
