import { defineEndpointTransport } from "./transportRuntime";
import type { EndpointTransportBindingMetadata, TransportCallOptions } from "./transportTypes";
import { mapUnknownError } from "./errorRuntime";
import type { FrontendDomainError } from "./errorTypes";
import { resolveAvailability, resolveEndpointAvailability } from "./availabilityRuntime";
import type { AvailabilityDescriptor, AvailabilityState } from "./availabilityTypes";
import { sharedRealtimeRegistry } from "../shared/realtime.generated";
import { createLinkedAbortController } from "./abortRuntime";

export interface MutationBindingOptions<TInput, TOutput> {
  endpointKey: string;
  transportMetadata: EndpointTransportBindingMetadata;
  invalidatesEndpointKeys: readonly string[];
  realtimeLinks: readonly string[];
  availability: AvailabilityDescriptor;
  errorRefs: readonly string[];
}

export interface MutationExecution<TOutput> {
  promise: Promise<TOutput>;
  cancel: () => void;
  affectedEndpointKeys: readonly string[];
  invalidatedByRealtimeEventKeys: readonly string[];
}

export interface MutationBinding<TInput, TOutput> {
  readonly endpointKey: string;
  readonly getAvailability: () => AvailabilityState;
  readonly getAvailabilityRefs: () => AvailabilityDescriptor;
  readonly getErrorRefs: () => readonly string[];
  readonly execute: (input: TInput, options?: TransportCallOptions) => MutationExecution<TOutput>;
  readonly invalidatesEndpointKeys: readonly string[];
  readonly realtimeLinks: readonly string[];
  readonly getInvalidatedByRealtimeEventKeys: () => readonly string[];
  readonly getAffectedEndpointKeys: () => readonly string[];
}

interface RealtimeRegistryLike {
  resolveAffectedEndpointKeys: (realtimeKey: string) => readonly string[];
}

const realtimeRegistry = sharedRealtimeRegistry as unknown as RealtimeRegistryLike;

export function defineMutationBinding<TInput, TOutput>(
  options: MutationBindingOptions<TInput, TOutput>,
): MutationBinding<TInput, TOutput> {
  const transport = defineEndpointTransport<TInput, TOutput>(options.transportMetadata);
  const invalidatedByRealtimeEventKeys = options.transportMetadata.invalidatedByRealtimeEventKeys;
  const affectedEndpointKeys = resolveMutationAffectedEndpointKeys(options.invalidatesEndpointKeys, invalidatedByRealtimeEventKeys);

  return {
    endpointKey: options.endpointKey,
    getAvailability: () => resolveBindingAvailability(options.endpointKey, options.availability),
    getAvailabilityRefs: () => options.availability,
    getErrorRefs: () => options.errorRefs,
    invalidatesEndpointKeys: options.invalidatesEndpointKeys,
    realtimeLinks: options.realtimeLinks,
    getInvalidatedByRealtimeEventKeys: () => invalidatedByRealtimeEventKeys,
    getAffectedEndpointKeys: () => affectedEndpointKeys,
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
        affectedEndpointKeys,
        invalidatedByRealtimeEventKeys,
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

function resolveMutationAffectedEndpointKeys(
  invalidatesEndpointKeys: readonly string[],
  invalidatedByRealtimeEventKeys: readonly string[],
): readonly string[] {
  const affected = new Set<string>(invalidatesEndpointKeys);
  for (const realtimeKey of invalidatedByRealtimeEventKeys) {
    for (const endpointKey of realtimeRegistry.resolveAffectedEndpointKeys(realtimeKey)) {
      affected.add(endpointKey);
    }
  }

  return Array.from(affected);
}
