import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerSuggestTransport.metadata.generated.json";
import type { StaffPositionSuggestionDto } from "../staffpositions/types/StaffPositionSuggestionDto.generated";import type { SuggestStaffPositionRequest } from "../staffpositions/types/SuggestStaffPositionRequest.generated";
export const staffPositionControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestStaffPositionRequest; }, StaffPositionSuggestionDto[]>(staffPositionControllerSuggestTransportMetadata);
