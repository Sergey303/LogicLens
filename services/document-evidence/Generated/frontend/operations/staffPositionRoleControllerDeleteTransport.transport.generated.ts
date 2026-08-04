import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionRoleControllerDeleteTransport.metadata.generated.json";

export const staffPositionRoleControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionRoleControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(staffPositionRoleControllerDeleteTransportMetadata);
