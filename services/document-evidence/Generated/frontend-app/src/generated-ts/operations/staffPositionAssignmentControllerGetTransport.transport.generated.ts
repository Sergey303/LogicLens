import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerGetTransport.metadata.generated.json";
import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";
export const staffPositionAssignmentControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerGetTransport = defineEndpointTransport<{ id: string; }, StaffPositionAssignmentDto>(staffPositionAssignmentControllerGetTransportMetadata);
