import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerSuggestTransport.metadata.generated.json";
import type { DocumentRevisionSuggestionDto } from "../documentrevisions/types/DocumentRevisionSuggestionDto.generated";import type { SuggestDocumentRevisionRequest } from "../documentrevisions/types/SuggestDocumentRevisionRequest.generated";
export const documentRevisionControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestDocumentRevisionRequest; }, DocumentRevisionSuggestionDto[]>(documentRevisionControllerSuggestTransportMetadata);
