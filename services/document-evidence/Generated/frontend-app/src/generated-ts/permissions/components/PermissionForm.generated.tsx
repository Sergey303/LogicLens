// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreatePermissionRequest } from "../types/CreatePermissionRequest.generated";
import type { UpdatePermissionRequest } from "../types/UpdatePermissionRequest.generated";
import { PermissionField } from "./PermissionField.generated";

export type PermissionFormValue = CreatePermissionRequest | UpdatePermissionRequest;

export interface PermissionFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface PermissionFormProps<TValue extends PermissionFormValue = PermissionFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly PermissionFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function PermissionForm<TValue extends PermissionFormValue>(props: PermissionFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <PermissionField
        id="permission-code"
        label="Code"
        kind="text"
        value={props.value["code"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["code"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["code"]: nextValue as TValue["code"],
          });
        }}
      />
      <PermissionField
        id="permission-name"
        label="Name"
        kind="text"
        value={props.value["name"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["name"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["name"]: nextValue as TValue["name"],
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
