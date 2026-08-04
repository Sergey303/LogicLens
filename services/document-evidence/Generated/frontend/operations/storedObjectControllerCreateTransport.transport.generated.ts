import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerCreateTransport.metadata.generated.json";
import type { CreateStoredObjectRequest } from "../storedobjects/types/CreateStoredObjectRequest.generated";import type { StoredObjectDto } from "../storedobjects/types/StoredObjectDto.generated";
export const storedObjectControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerCreateTransport = defineEndpointTransport<CreateStoredObjectRequest, StoredObjectDto>(storedObjectControllerCreateTransportMetadata);
