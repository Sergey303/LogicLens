// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateProcessingJobRequest } from "../types/CreateProcessingJobRequest.generated";
import type { UpdateProcessingJobRequest } from "../types/UpdateProcessingJobRequest.generated";
import { ProcessingJobField } from "./ProcessingJobField.generated";

export type ProcessingJobFormValue = CreateProcessingJobRequest | UpdateProcessingJobRequest;

export interface ProcessingJobFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface ProcessingJobFormProps<TValue extends ProcessingJobFormValue = ProcessingJobFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly ProcessingJobFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function ProcessingJobForm<TValue extends ProcessingJobFormValue>(props: ProcessingJobFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <ProcessingJobField
        id="processingjob-attempt"
        label="Attempt"
        kind="number"
        value={props.value["attempt"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["attempt"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["attempt"]: nextValue as TValue["attempt"],
          });
        }}
      />
      <ProcessingJobField
        id="processingjob-documentrevisionid"
        label="Document Revision Id"
        kind="text"
        value={props.value["documentRevisionId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["documentRevisionId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["documentRevisionId"]: nextValue as TValue["documentRevisionId"],
          });
        }}
      />
      <ProcessingJobField
        id="processingjob-idempotencykey"
        label="Idempotency Key"
        kind="text"
        value={props.value["idempotencyKey"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["idempotencyKey"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["idempotencyKey"]: nextValue as TValue["idempotencyKey"],
          });
        }}
      />
      <ProcessingJobField
        id="processingjob-kind"
        label="Kind"
        kind="text"
        value={props.value["kind"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["kind"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["kind"]: nextValue as TValue["kind"],
          });
        }}
      />
      <ProcessingJobField
        id="processingjob-lasterrorcode"
        label="Last Error Code"
        kind="text"
        value={props.value["lastErrorCode"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["lastErrorCode"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["lastErrorCode"]: nextValue as TValue["lastErrorCode"],
          });
        }}
      />
      <ProcessingJobField
        id="processingjob-leaseuntil"
        label="Lease Until"
        kind="date"
        value={props.value["leaseUntil"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["leaseUntil"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["leaseUntil"]: nextValue as TValue["leaseUntil"],
          });
        }}
      />
      <ProcessingJobField
        id="processingjob-state"
        label="State"
        kind="text"
        value={props.value["state"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["state"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["state"]: nextValue as TValue["state"],
          });
        }}
      />
      <div className="appforge-generated-form-actions">
        <Button
          type="submit"
          label={props.submitLabel ?? "Save"}
          loading={props.submitting}
          disabled={disabled}
        />
      </div>
    </form>
  );
}
