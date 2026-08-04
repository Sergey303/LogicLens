import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerDeleteTransport.metadata.generated.json";

export const documentFragmentControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(documentFragmentControllerDeleteTransportMetadata);
