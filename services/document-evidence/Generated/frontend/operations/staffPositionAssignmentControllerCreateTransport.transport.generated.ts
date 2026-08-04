import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerCreateTransport.metadata.generated.json";
import type { CreateStaffPositionAssignmentRequest } from "../staffpositionassignments/types/CreateStaffPositionAssignmentRequest.generated";import type { StaffPositionAssignmentDto } from "../staffpositionassignments/types/StaffPositionAssignmentDto.generated";
export const staffPositionAssignmentControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerCreateTransport = defineEndpointTransport<CreateStaffPositionAssignmentRequest, StaffPositionAssignmentDto>(staffPositionAssignmentControllerCreateTransportMetadata);
