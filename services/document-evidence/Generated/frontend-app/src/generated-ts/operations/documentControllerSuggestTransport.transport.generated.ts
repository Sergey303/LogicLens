import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerSuggestTransport.metadata.generated.json";
import type { DocumentSuggestionDto } from "../documents/types/DocumentSuggestionDto.generated";import type { SuggestDocumentRequest } from "../documents/types/SuggestDocumentRequest.generated";
export const documentControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestDocumentRequest; }, DocumentSuggestionDto[]>(documentControllerSuggestTransportMetadata);
