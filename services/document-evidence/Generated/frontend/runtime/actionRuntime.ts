import {
  defineEndpointTransport,
} from "./transportRuntime";
import type {
  EndpointTransportBindingMetadata,
  FrontendActionMetadata,
  TransportCallOptions,
} from "./transportTypes";
import { performFrontendAction } from "./actionFrontendEffects";
import { mapUnknownError } from "./errorRuntime";
import type { FrontendDomainError } from "./errorTypes";
import { resolveAvailability, resolveEndpointAvailability } from "./availabilityRuntime";
import type { AvailabilityDescriptor, AvailabilityState } from "./availabilityTypes";
import { sharedRealtimeRegistry } from "../shared/realtime.generated";
import { createLinkedAbortController } from "./abortRuntime";

export interface ActionBindingOptions<TInput, TOutput> {
  endpointKey: string;
  transportMetadata: EndpointTransportBindingMetadata;
  frontendAction: FrontendActionMetadata | null;
  invalidatesEndpointKeys: readonly string[];
  realtimeLinks: readonly string[];
  availability: AvailabilityDescriptor;
  errorRefs: readonly string[];
}

export interface ActionExecution<TOutput> {
  promise: Promise<TOutput>;
  cancel: () => void;
  affectedEndpointKeys: readonly string[];
  invalidatedByRealtimeEventKeys: readonly string[];
}

export interface ActionBinding<TInput, TOutput> {
  readonly endpointKey: string;
  readonly getAvailability: () => AvailabilityState;
  readonly getAvailabilityRefs: () => AvailabilityDescriptor;
  readonly getErrorRefs: () => readonly string[];
  readonly execute: (input: TInput, options?: TransportCallOptions) => ActionExecution<TOutput>;
  readonly frontendAction: FrontendActionMetadata | null;
  readonly invalidatesEndpointKeys: readonly string[];
  readonly realtimeLinks: readonly string[];
  readonly getInvalidatedByRealtimeEventKeys: () => readonly string[];
  readonly getAffectedEndpointKeys: () => readonly string[];
}

interface RealtimeRegistryLike {
  resolveAffectedEndpointKeys: (realtimeKey: string) => readonly string[];
}

const realtimeRegistry = sharedRealtimeRegistry as unknown as RealtimeRegistryLike;

export function defineActionBinding<TInput, TOutput>(
  options: ActionBindingOptions<TInput, TOutput>,
): ActionBinding<TInput, TOutput> {
  const transport = defineEndpointTransport<TInput, TOutput>(options.transportMetadata);
  const invalidatedByRealtimeEventKeys = options.transportMetadata.invalidatedByRealtimeEventKeys;
  const affectedEndpointKeys = resolveActionAffectedEndpointKeys(options.invalidatesEndpointKeys, invalidatedByRealtimeEventKeys);

  return {
    endpointKey: options.endpointKey,
    getAvailability: () => resolveBindingAvailability(options.endpointKey, options.availability),
    getAvailabilityRefs: () => options.availability,
    getErrorRefs: () => options.errorRefs,
    frontendAction: options.frontendAction,
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

      const promise = transport(input, transportOptions)
        .then((result) => {
          performFrontendAction(options.frontendAction, result);
          return result;
        })
        .catch((error) => {
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

function resolveActionAffectedEndpointKeys(
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
