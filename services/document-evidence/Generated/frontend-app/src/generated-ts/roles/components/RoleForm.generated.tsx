// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateRoleRequest } from "../types/CreateRoleRequest.generated";
import type { UpdateRoleRequest } from "../types/UpdateRoleRequest.generated";
import { RoleField } from "./RoleField.generated";

export type RoleFormValue = CreateRoleRequest | UpdateRoleRequest;

export interface RoleFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface RoleFormProps<TValue extends RoleFormValue = RoleFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly RoleFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function RoleForm<TValue extends RoleFormValue>(props: RoleFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <RoleField
        id="role-code"
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
      <RoleField
        id="role-name"
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
