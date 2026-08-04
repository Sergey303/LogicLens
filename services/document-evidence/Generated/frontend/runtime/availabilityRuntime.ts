import {
  generatedDisabledReasonMessagesByKey,
  generatedDeploymentFeatureStatesByKey,
  generatedDeploymentPolicyStatesByKey,
  generatedEndpointAvailabilityByKey,
  generatedFeatureCatalogByKey,
  generatedPolicyCatalogByKey,
} from "./availabilityData";
import {
  getRuntimeEndpointAvailability,
  getRuntimeFeatureState,
  getRuntimePolicyState,
  resolveRuntimeDisabledReasonMessage,
} from "./availabilityRuntimeState";
import type {
  AvailabilityDescriptor,
  AvailabilityState,
  ResolvedFeatureAvailability,
  ResolvedPolicyAvailability,
} from "./availabilityTypes";

export function resolveAvailability(descriptor: AvailabilityDescriptor): AvailabilityState {
  const featureStates = descriptor.featureKeys.map(resolveFeatureAvailability);
  const policyStates = descriptor.policyKeys.map(resolvePolicyAvailability);
  return {
    isVisible: featureStates.every((state) => state.visible),
    isEnabled: featureStates.every((state) => state.enabled) && policyStates.every((state) => state.enabled),
    disabledReason: resolveDisabledReason(featureStates, policyStates),
  };
}

export function resolveEndpointAvailability(endpointKey: string): AvailabilityState {
  const descriptor = getRuntimeEndpointAvailability(endpointKey) ?? generatedEndpointAvailabilityByKey[endpointKey];
  return descriptor ? resolveAvailability(descriptor) : visibleEnabled();
}

function visibleEnabled(): AvailabilityState {
  return {
    isVisible: true,
    isEnabled: true,
    disabledReason: null,
  };
}

function resolveFeatureAvailability(featureKey: string): ResolvedFeatureAvailability {
  const explicitState = getRuntimeFeatureState(featureKey) ?? generatedDeploymentFeatureStatesByKey[featureKey];
  if (explicitState) {
    return {
      featureKey,
      visible: explicitState.visible,
      enabled: explicitState.enabled,
      reasonKey: explicitState.reasonKey,
    };
  }

  const catalogEntry = generatedFeatureCatalogByKey[featureKey];
  return {
    featureKey,
    visible: catalogEntry ? catalogEntry.defaultVisibility !== "hidden" : true,
    enabled: catalogEntry ? catalogEntry.defaultEnabled !== false : true,
    reasonKey: null,
  };
}

function resolvePolicyAvailability(policyKey: string): ResolvedPolicyAvailability {
  const explicitState = getRuntimePolicyState(policyKey) ?? generatedDeploymentPolicyStatesByKey[policyKey];
  if (explicitState) {
    return {
      policyKey,
      enabled: explicitState.enabled,
      reasonKey: explicitState.reasonKey,
    };
  }

  void generatedPolicyCatalogByKey[policyKey];
  return {
    policyKey,
    enabled: true,
    reasonKey: null,
  };
}

function resolveDisabledReason(
  featureStates: readonly ResolvedFeatureAvailability[],
  policyStates: readonly ResolvedPolicyAvailability[],
): string | null {
  const reasonKey =
    featureStates.find((state) => state.reasonKey !== null && (!state.visible || !state.enabled))?.reasonKey ??
    policyStates.find((state) => state.reasonKey !== null && !state.enabled)?.reasonKey ??
    null;

  if (!reasonKey) {
    return null;
  }

  return resolveRuntimeDisabledReasonMessage(reasonKey) ?? generatedDisabledReasonMessagesByKey[reasonKey] ?? reasonKey;
}
