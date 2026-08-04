import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerUpdateTransport.metadata.generated.json";
import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";import type { UpdateStoredObjectRequest } from "../storedobjects/types/UpdateStoredObjectRequest.generated";
export const storedObjectControllerUpdateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerUpdateTransport = defineEndpointTransport<{ id: string; body: UpdateStoredObjectRequest; }, StoredObjectDto>(storedObjectControllerUpdateTransportMetadata);
