import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentControllerLookupTransport.metadata.generated.json";
import type { DocumentLookupDto } from "../documents/types/DocumentLookupDto.generated";import type { LookupDocumentRequest } from "../documents/types/LookupDocumentRequest.generated";
export const documentControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentControllerLookupTransport = defineEndpointTransport<{ request: LookupDocumentRequest; }, DocumentLookupDto[]>(documentControllerLookupTransportMetadata);
