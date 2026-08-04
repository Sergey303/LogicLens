export interface AvailabilityDescriptor {
  featureKeys: readonly string[];
  policyKeys: readonly string[];
  capabilityKeys?: readonly string[];
  providerKeys?: readonly string[];
  environmentScopes?: readonly string[];
  disabledReasonKey?: string | null;
}

export interface AvailabilityState {
  isVisible: boolean;
  isEnabled: boolean;
  disabledReason: string | null;
}

export interface DeploymentFeatureState {
  featureKey: string;
  domainKey?: string;
  visible: boolean;
  enabled: boolean;
  reasonKey: string | null;
  sourceKind: string;
}

export interface DeploymentPolicyState {
  policyKey: string;
  domainKey?: string;
  enabled: boolean;
  reasonKey: string | null;
  sourceKind: string;
}

export interface DeploymentCapabilityState {
  capabilityKey: string;
  enabled: boolean;
  reasonKey: string | null;
  sourceKind: string;
}

export interface DeploymentProviderState {
  providerKey: string;
  enabled: boolean;
  reasonKey: string | null;
  sourceKind: string;
}

export interface FeatureCatalogEntry {
  featureKey: string;
  defaultVisibility: string;
  defaultEnabled: boolean;
}

export interface PolicyCatalogEntry {
  policyKey: string;
  policyKind: string;
}

export interface ResolvedFeatureAvailability {
  featureKey: string;
  visible: boolean;
  enabled: boolean;
  reasonKey: string | null;
}

export interface ResolvedPolicyAvailability {
  policyKey: string;
  enabled: boolean;
  reasonKey: string | null;
}

export interface AvailabilityRuntimeSnapshot {
  featureStatesByKey?: Record<string, DeploymentFeatureState>;
  policyStatesByKey?: Record<string, DeploymentPolicyState>;
  endpointAvailabilityByKey?: Record<string, AvailabilityDescriptor>;
  disabledReasonMessagesByKey?: Record<string, string>;
}
