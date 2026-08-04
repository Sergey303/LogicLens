import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerListTransport.metadata.generated.json";
import type { ListDocumentRequest } from "../documents/types/ListDocumentRequest.generated";import type { ListDocumentResult } from "../documents/types/ListDocumentResult.generated";
export const documentControllerListTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerListTransport = defineEndpointTransport<{ request: ListDocumentRequest; }, ListDocumentResult>(documentControllerListTransportMetadata);
