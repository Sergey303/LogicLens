import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerOptionsTransport.metadata.generated.json";
import type { StaffPositionAssignmentOptionDto } from "../staffpositionassignments/types/StaffPositionAssignmentOptionDto.generated";
export const staffPositionAssignmentControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerOptionsTransport = defineEndpointTransport<{ field: string; }, StaffPositionAssignmentOptionDto[]>(staffPositionAssignmentControllerOptionsTransportMetadata);
