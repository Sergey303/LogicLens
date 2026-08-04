import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerCreateTransport.metadata.generated.json";
import type { CreateProcessingJobRequest } from "../processingjobs/types/CreateProcessingJobRequest.generated";import type { ProcessingJobDto } from "../processingjobs/types/ProcessingJobDto.generated";
export const processingJobControllerCreateTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerCreateTransport = defineEndpointTransport<CreateProcessingJobRequest, ProcessingJobDto>(processingJobControllerCreateTransportMetadata);
