import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerSuggestTransport.metadata.generated.json";
import type { StaffPositionRoleSuggestionDto } from "../staffpositionroles/types/StaffPositionRoleSuggestionDto.generated";import type { SuggestStaffPositionRoleRequest } from "../staffpositionroles/types/SuggestStaffPositionRoleRequest.generated";
export const staffPositionRoleControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestStaffPositionRoleRequest; }, StaffPositionRoleSuggestionDto[]>(staffPositionRoleControllerSuggestTransportMetadata);
