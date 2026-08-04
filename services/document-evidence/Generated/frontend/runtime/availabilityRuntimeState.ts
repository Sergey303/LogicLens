import type {
  AvailabilityDescriptor,
  AvailabilityRuntimeSnapshot,
  DeploymentFeatureState,
  DeploymentPolicyState,
} from "./availabilityTypes";

let runtimeFeatureStatesByKey: Record<string, DeploymentFeatureState> = {};
let runtimePolicyStatesByKey: Record<string, DeploymentPolicyState> = {};
let runtimeEndpointAvailabilityByKey: Record<string, AvailabilityDescriptor> = {};
let runtimeDisabledReasonMessagesByKey: Record<string, string> = {};

export function configureAvailabilityRuntimeSnapshot(snapshot: AvailabilityRuntimeSnapshot | null): void {
  runtimeFeatureStatesByKey = snapshot?.featureStatesByKey ?? {};
  runtimePolicyStatesByKey = snapshot?.policyStatesByKey ?? {};
  runtimeEndpointAvailabilityByKey = snapshot?.endpointAvailabilityByKey ?? {};
  runtimeDisabledReasonMessagesByKey = snapshot?.disabledReasonMessagesByKey ?? {};
}

export function getRuntimeFeatureState(featureKey: string): DeploymentFeatureState | undefined {
  return runtimeFeatureStatesByKey[featureKey];
}

export function getRuntimePolicyState(policyKey: string): DeploymentPolicyState | undefined {
  return runtimePolicyStatesByKey[policyKey];
}

export function getRuntimeEndpointAvailability(endpointKey: string): AvailabilityDescriptor | undefined {
  return runtimeEndpointAvailabilityByKey[endpointKey];
}

export function resolveRuntimeDisabledReasonMessage(reasonKey: string): string | undefined {
  return runtimeDisabledReasonMessagesByKey[reasonKey];
}
