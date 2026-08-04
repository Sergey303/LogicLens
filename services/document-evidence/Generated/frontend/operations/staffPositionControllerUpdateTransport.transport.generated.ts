import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerUpdateTransport.metadata.generated.json";
import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";import type { UpdateStaffPositionRequest } from "../staffpositions/types/UpdateStaffPositionRequest.generated";
export const staffPositionControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateStaffPositionRequest; }, StaffPositionDto>(staffPositionControllerUpdateTransportMetadata);
