import { disabledReasonMessagesByKey } from "../shared/contracts/availability/disabledReasonMessages.generated";
import { deploymentFeatureStatesByKey } from "../shared/contracts/availability/deploymentFeatureStates.generated";
import { deploymentPolicyStatesByKey } from "../shared/contracts/availability/deploymentPolicyStates.generated";
import { endpointAvailabilityByKey } from "../shared/contracts/availability/endpointAvailability.generated";
import { featureAvailabilityCatalogByKey } from "../shared/contracts/availability/featureAvailabilityCatalog.generated";
import { policyAvailabilityCatalogByKey } from "../shared/contracts/availability/policyAvailabilityCatalog.generated";
import type {
  AvailabilityDescriptor,
  DeploymentFeatureState,
  DeploymentPolicyState,
  FeatureCatalogEntry,
  PolicyCatalogEntry,
} from "./availabilityTypes";

export const generatedFeatureCatalogByKey =
  featureAvailabilityCatalogByKey as Record<string, FeatureCatalogEntry>;
export const generatedPolicyCatalogByKey =
  policyAvailabilityCatalogByKey as Record<string, PolicyCatalogEntry>;
export const generatedDeploymentFeatureStatesByKey =
  deploymentFeatureStatesByKey as Record<string, DeploymentFeatureState>;
export const generatedDeploymentPolicyStatesByKey =
  deploymentPolicyStatesByKey as Record<string, DeploymentPolicyState>;
export const generatedDisabledReasonMessagesByKey =
  disabledReasonMessagesByKey as Record<string, string>;
export const generatedEndpointAvailabilityByKey =
  endpointAvailabilityByKey as Record<string, AvailabilityDescriptor>;
