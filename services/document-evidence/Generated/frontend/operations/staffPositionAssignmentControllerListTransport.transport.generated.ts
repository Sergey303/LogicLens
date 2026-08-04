import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerListTransport.metadata.generated.json";
import type { ListStaffPositionAssignmentRequest } from "../staffpositionassignments/types/ListStaffPositionAssignmentRequest.generated";import type { ListStaffPositionAssignmentResult } from "../staffpositionassignments/types/ListStaffPositionAssignmentResult.generated";
export const staffPositionAssignmentControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerListTransport = defineEndpointTransport<{ request: ListStaffPositionAssignmentRequest; }, ListStaffPositionAssignmentResult>(staffPositionAssignmentControllerListTransportMetadata);
