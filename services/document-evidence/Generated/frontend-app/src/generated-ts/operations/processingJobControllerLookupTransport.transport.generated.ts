import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerLookupTransport.metadata.generated.json";
import type { LookupProcessingJobRequest } from "../processingjobs/types/LookupProcessingJobRequest.generated";import type { ProcessingJobLookupDto } from "../processingjobs/types/ProcessingJobLookupDto.generated";
export const processingJobControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerLookupTransport = defineEndpointTransport<{ request: LookupProcessingJobRequest; }, ProcessingJobLookupDto[]>(processingJobControllerLookupTransportMetadata);
