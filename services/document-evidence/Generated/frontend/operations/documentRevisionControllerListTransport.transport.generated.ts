import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerListTransport.metadata.generated.json";
import type { ListDocumentRevisionRequest } from "../documentrevisions/types/ListDocumentRevisionRequest.generated";import type { ListDocumentRevisionResult } from "../documentrevisions/types/ListDocumentRevisionResult.generated";
export const documentRevisionControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerListTransport = defineEndpointTransport<{ request: ListDocumentRevisionRequest; }, ListDocumentRevisionResult>(documentRevisionControllerListTransportMetadata);
