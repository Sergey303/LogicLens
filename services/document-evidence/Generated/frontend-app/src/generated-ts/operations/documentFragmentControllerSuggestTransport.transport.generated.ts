import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentFragmentControllerSuggestTransport.metadata.generated.json";
import type { DocumentFragmentSuggestionDto } from "../documentfragments/types/DocumentFragmentSuggestionDto.generated";import type { SuggestDocumentFragmentRequest } from "../documentfragments/types/SuggestDocumentFragmentRequest.generated";
export const documentFragmentControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentFragmentControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestDocumentFragmentRequest; }, DocumentFragmentSuggestionDto[]>(documentFragmentControllerSuggestTransportMetadata);
