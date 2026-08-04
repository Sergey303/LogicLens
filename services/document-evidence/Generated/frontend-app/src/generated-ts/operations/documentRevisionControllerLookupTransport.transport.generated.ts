import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/documentRevisionControllerLookupTransport.metadata.generated.json";
import type { DocumentRevisionLookupDto } from "../documentrevisions/types/DocumentRevisionLookupDto.generated";import type { LookupDocumentRevisionRequest } from "../documentrevisions/types/LookupDocumentRevisionRequest.generated";
export const documentRevisionControllerLookupTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const documentRevisionControllerLookupTransport = defineEndpointTransport<{ request: LookupDocumentRevisionRequest; }, DocumentRevisionLookupDto[]>(documentRevisionControllerLookupTransportMetadata);
