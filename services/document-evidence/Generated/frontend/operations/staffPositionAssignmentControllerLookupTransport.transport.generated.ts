import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerLookupTransport.metadata.generated.json";
import type { LookupStaffPositionAssignmentRequest } from "../staffpositionassignments/types/LookupStaffPositionAssignmentRequest.generated";import type { StaffPositionAssignmentLookupDto } from "../staffpositionassignments/types/StaffPositionAssignmentLookupDto.generated";
export const staffPositionAssignmentControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerLookupTransport = defineEndpointTransport<{ request: LookupStaffPositionAssignmentRequest; }, StaffPositionAssignmentLookupDto[]>(staffPositionAssignmentControllerLookupTransportMetadata);
