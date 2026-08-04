import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerGetTransport.metadata.generated.json";
import type { StaffPositionDto } from "../staffpositions/types/StaffPositionDto.generated";
export const staffPositionControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerGetTransport = defineEndpointTransport<{ id: string; }, StaffPositionDto>(staffPositionControllerGetTransportMetadata);
