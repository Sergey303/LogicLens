import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerLookupTransport.metadata.generated.json";
import type { LookupStaffPositionRequest } from "../staffpositions/types/LookupStaffPositionRequest.generated";import type { StaffPositionLookupDto } from "../staffpositions/types/StaffPositionLookupDto.generated";
export const staffPositionControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerLookupTransport = defineEndpointTransport<{ request: LookupStaffPositionRequest; }, StaffPositionLookupDto[]>(staffPositionControllerLookupTransportMetadata);
