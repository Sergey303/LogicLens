import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerUpdateTransport.metadata.generated.json";
import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";import type { UpdateStaffPositionAssignmentRequest } from "../staffpositionassignments/types/UpdateStaffPositionAssignmentRequest.generated";
export const staffPositionAssignmentControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateStaffPositionAssignmentRequest; }, StaffPositionAssignmentDto>(staffPositionAssignmentControllerUpdateTransportMetadata);
