import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerListTransport.metadata.generated.json";
import type { ListStaffPositionRoleRequest } from "../staffpositionroles/types/ListStaffPositionRoleRequest.generated";import type { ListStaffPositionRoleResult } from "../staffpositionroles/types/ListStaffPositionRoleResult.generated";
export const staffPositionRoleControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerListTransport = defineEndpointTransport<{ request: ListStaffPositionRoleRequest; }, ListStaffPositionRoleResult>(staffPositionRoleControllerListTransportMetadata);
