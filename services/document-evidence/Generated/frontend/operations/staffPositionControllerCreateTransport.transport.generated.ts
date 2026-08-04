import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerCreateTransport.metadata.generated.json";
import type { CreateStaffPositionRequest } from "../staffpositions/types/CreateStaffPositionRequest.generated";import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";
export const staffPositionControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerCreateTransport = defineEndpointTransport<CreateStaffPositionRequest, StaffPositionDto>(staffPositionControllerCreateTransportMetadata);
