import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerSuggestTransport.metadata.generated.json";
import type { ProcessingJobSuggestionDto } from "../processingjobs/types/ProcessingJobSuggestionDto.generated";import type { SuggestProcessingJobRequest } from "../processingjobs/types/SuggestProcessingJobRequest.generated";
export const processingJobControllerSuggestTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerSuggestTransport = defineEndpointTransport<{ field: string; request: SuggestProcessingJobRequest; }, ProcessingJobSuggestionDto[]>(processingJobControllerSuggestTransportMetadata);
