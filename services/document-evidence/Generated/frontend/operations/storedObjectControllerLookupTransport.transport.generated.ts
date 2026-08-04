import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerLookupTransport.metadata.generated.json";
import type { LookupStoredObjectRequest } from "../storedobjects/types/LookupStoredObjectRequest.generated";import type { StoredObjectLookupDto } from "../storedobjects/types/StoredObjectLookupDto.generated";
export const storedObjectControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerLookupTransport = defineEndpointTransport<{ request: LookupStoredObjectRequest; }, StoredObjectLookupDto[]>(storedObjectControllerLookupTransportMetadata);
