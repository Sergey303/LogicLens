import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerSuggestTransport.metadata.generated.json";
import type { StoredObjectSuggestionDto } from "../storedobjects/types/StoredObjectSuggestionDto.generated";import type { SuggestStoredObjectRequest } from "../storedobjects/types/SuggestStoredObjectRequest.generated";
export const storedObjectControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestStoredObjectRequest; }, StoredObjectSuggestionDto[]>(storedObjectControllerSuggestTransportMetadata);
