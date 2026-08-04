import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerSuggestTransport.metadata.generated.json";
import type { StaffPositionAssignmentSuggestionDto } from "../staffpositionassignments/types/StaffPositionAssignmentSuggestionDto.generated";import type { SuggestStaffPositionAssignmentRequest } from "../staffpositionassignments/types/SuggestStaffPositionAssignmentRequest.generated";
export const staffPositionAssignmentControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestStaffPositionAssignmentRequest; }, StaffPositionAssignmentSuggestionDto[]>(staffPositionAssignmentControllerSuggestTransportMetadata);
