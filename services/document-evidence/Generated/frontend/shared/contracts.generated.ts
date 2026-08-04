// ------------------------------------------------------------------------------
// GENERATED FILE - source: shared/contracts.generated.ts
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

export type BackendContractDomainKey =
  typeof import("../meta/domains.generated").generatedDomains[number];

export type BackendContractEndpointDescriptor =
  Record<string, unknown> & { endpointKey: string; kind: string };
export type BackendContractRealtimeDescriptor =
  Record<string, unknown> & { realtimeKey: string; kind: string };
export type BackendContractEndpointKey = string;
export type BackendContractQueryEndpointKey = string;
export type BackendContractMutationEndpointKey = string;
export type BackendContractActionEndpointKey = string;
export type BackendContractRealtimeEventKey = string;
export type BackendContractRealtimeCommandKey = string;
export type BackendContractRealtimeKey = string;
export type BackendContractQueryEndpointDescriptor =
  BackendContractEndpointDescriptor;
export type BackendContractMutationEndpointDescriptor =
  BackendContractEndpointDescriptor;
export type BackendContractActionEndpointDescriptor =
  BackendContractEndpointDescriptor;
