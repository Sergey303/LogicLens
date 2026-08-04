import { TransportRuntimeError, unsupportedBindingSourceError } from "./transportErrors";
import type {
  EndpointTransportBindingMetadata,
  EndpointTransportInput,
  ResolvedTransportInput,
  SupportedBindingSource,
} from "./transportTypes";
import { asInputRecord } from "./transportWireValues";

export function resolveTransportInputs<TRequest>(
  metadata: EndpointTransportBindingMetadata,
  input: TRequest,
): readonly ResolvedTransportInput[] {
  const inputRecord = asInputRecord(input);

  return metadata.transport.inputs.map((transportInput) => {
    const bindingSource = transportInput.bindingSource as SupportedBindingSource;
    if (!isSupportedBindingSource(bindingSource)) {
      throw unsupportedBindingSourceError(transportInput.bindingSource, metadata);
    }

    const resolvedValue = resolveInputValue(inputRecord, transportInput);
    if (isMissingInputValue(resolvedValue.value, transportInput)) {
      throw new TransportRuntimeError(
        `[transportRuntime] Missing required ${bindingSource} input '${transportInput.inputKey}' for endpoint '${metadata.endpointKey}'.`,
      );
    }

    return {
      metadata: transportInput,
      value: resolvedValue.value,
      matchedKey: resolvedValue.matchedKey,
    };
  });
}

function resolveInputValue(
  inputRecord: Record<string, unknown> | null,
  transportInput: EndpointTransportInput,
): { value: unknown; matchedKey: string | null } {
  const candidates = [transportInput.inputKey, transportInput.name, transportInput.wireName];

  if (!inputRecord) {
    return { value: undefined, matchedKey: null };
  }

  for (const candidate of candidates) {
    if (Object.prototype.hasOwnProperty.call(inputRecord, candidate)) {
      return { value: inputRecord[candidate], matchedKey: candidate };
    }
  }

  return { value: undefined, matchedKey: null };
}

function isMissingInputValue(value: unknown, inputMetadata: EndpointTransportInput): boolean {
  if (value === undefined) {
    return inputMetadata.required;
  }

  if (value === null && !inputMetadata.nullable) {
    return inputMetadata.required;
  }

  return false;
}

function isSupportedBindingSource(value: string): value is SupportedBindingSource {
  return value === "route" || value === "query" || value === "header" || value === "form";
}
