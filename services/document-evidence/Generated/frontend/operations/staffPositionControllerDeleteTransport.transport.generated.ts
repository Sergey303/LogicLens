import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionControllerDeleteTransport.metadata.generated.json";

export const staffPositionControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(staffPositionControllerDeleteTransportMetadata);
