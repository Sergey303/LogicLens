import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/storedObjectControllerOptionsTransport.metadata.generated.json";
import type { StoredObjectOptionDto } from "../storedobjects/types/StoredObjectOptionDto.generated";
export const storedObjectControllerOptionsTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const storedObjectControllerOptionsTransport = defineEndpointTransport<{ field: string; }, StoredObjectOptionDto[]>(storedObjectControllerOptionsTransportMetadata);
