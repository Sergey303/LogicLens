import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerOptionsTransport.metadata.generated.json";
import type { StaffPositionOptionDto } from "../staffpositions/types/StaffPositionOptionDto.generated";
export const staffPositionControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerOptionsTransport = defineEndpointTransport<{ field: string; }, StaffPositionOptionDto[]>(staffPositionControllerOptionsTransportMetadata);
