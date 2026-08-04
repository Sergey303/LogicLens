import { defineEndpointTransport } from "../runtime/transportRuntime";
import type { EndpointTransportBindingMetadata } from "../runtime/transportTypes";
import metadataJson from "./data/staffPositionAssignmentControllerDeleteTransport.metadata.generated.json";

export const staffPositionAssignmentControllerDeleteTransportMetadata = metadataJson as EndpointTransportBindingMetadata;

export const staffPositionAssignmentControllerDeleteTransport = defineEndpointTransport<{ id: string; }, void>(staffPositionAssignmentControllerDeleteTransportMetadata);
