import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerListTransport.metadata.generated.json";
import type { ListStoredObjectRequest } from "../storedobjects/types/ListStoredObjectRequest.generated";import type { ListStoredObjectResult } from "../storedobjects/types/ListStoredObjectResult.generated";
export const storedObjectControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerListTransport = defineEndpointTransport<{ request: ListStoredObjectRequest; }, ListStoredObjectResult>(storedObjectControllerListTransportMetadata);
