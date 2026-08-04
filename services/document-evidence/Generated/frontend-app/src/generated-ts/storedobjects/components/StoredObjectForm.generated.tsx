// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateStoredObjectRequest } from "../types/CreateStoredObjectRequest.generated";
import type { UpdateStoredObjectRequest } from "../types/UpdateStoredObjectRequest.generated";
import { StoredObjectField } from "./StoredObjectField.generated";

export type StoredObjectFormValue = CreateStoredObjectRequest | UpdateStoredObjectRequest;

export interface StoredObjectFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface StoredObjectFormProps<TValue extends StoredObjectFormValue = StoredObjectFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly StoredObjectFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function StoredObjectForm<TValue extends StoredObjectFormValue>(props: StoredObjectFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <StoredObjectField
        id="storedobject-mediatype"
        label="Media Type"
        kind="text"
        value={props.value["mediaType"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["mediaType"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["mediaType"]: nextValue as TValue["mediaType"],
          });
        }}
      />
      <StoredObjectField
        id="storedobject-sha256"
        label="Sha256"
        kind="text"
        value={props.value["sha256"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["sha256"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["sha256"]: nextValue as TValue["sha256"],
          });
        }}
      />
      <StoredObjectField
        id="storedobject-sizebytes"
        label="Size Bytes"
        kind="number"
        value={props.value["sizeBytes"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["sizeBytes"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["sizeBytes"]: nextValue as TValue["sizeBytes"],
          });
        }}
      />
      <StoredObjectField
        id="storedobject-storagekey"
        label="Storage Key"
        kind="text"
        value={props.value["storageKey"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["storageKey"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["storageKey"]: nextValue as TValue["storageKey"],
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
