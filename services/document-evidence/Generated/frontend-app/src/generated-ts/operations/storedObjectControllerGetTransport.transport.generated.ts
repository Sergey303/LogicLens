import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerGetTransport.metadata.generated.json";
import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";
export const storedObjectControllerGetTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerGetTransport = defineEndpointTransport<{ id: string; }, StoredObjectDto>(storedObjectControllerGetTransportMetadata);
