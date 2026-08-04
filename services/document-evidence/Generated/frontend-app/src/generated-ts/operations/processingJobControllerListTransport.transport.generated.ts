import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/processingJobControllerListTransport.metadata.generated.json";
import type { ListProcessingJobRequest } from "../processingjobs/types/ListProcessingJobRequest.generated";import type { ListProcessingJobResult } from "../processingjobs/types/ListProcessingJobResult.generated";
export const processingJobControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const processingJobControllerListTransport = defineEndpointTransport<{ request: ListProcessingJobRequest; }, ListProcessingJobResult>(processingJobControllerListTransportMetadata);
