import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerUpdateTransport.metadata.generated.json";
import type { StaffPositionRoleDto } from "../staffpositionroles/types/StaffPositionRoleDto.generated";import type { UpdateStaffPositionRoleRequest } from "../staffpositionroles/types/UpdateStaffPositionRoleRequest.generated";
export const staffPositionRoleControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateStaffPositionRoleRequest; }, StaffPositionRoleDto>(staffPositionRoleControllerUpdateTransportMetadata);
