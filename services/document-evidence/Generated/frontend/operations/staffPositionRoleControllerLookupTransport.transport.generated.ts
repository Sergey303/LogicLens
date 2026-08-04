import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerLookupTransport.metadata.generated.json";
import type { LookupStaffPositionRoleRequest } from "../staffpositionroles/types/LookupStaffPositionRoleRequest.generated";import type { StaffPositionRoleLookupDto } from "../staffpositionroles/types/StaffPositionRoleLookupDto.generated";
export const staffPositionRoleControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerLookupTransport = defineEndpointTransport<{ request: LookupStaffPositionRoleRequest; }, StaffPositionRoleLookupDto[]>(staffPositionRoleControllerLookupTransportMetadata);
