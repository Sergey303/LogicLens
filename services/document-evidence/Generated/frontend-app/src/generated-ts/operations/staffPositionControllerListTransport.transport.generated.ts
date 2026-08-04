import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerListTransport.metadata.generated.json";
import type { ListStaffPositionRequest } from "../staffpositions/types/ListStaffPositionRequest.generated";import type { ListStaffPositionResult } from "../staffpositions/types/ListStaffPositionResult.generated";
export const staffPositionControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerListTransport = defineEndpointTransport<{ request: ListStaffPositionRequest; }, ListStaffPositionResult>(staffPositionControllerListTransportMetadata);
