// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateRolePermissionRequest } from "../types/CreateRolePermissionRequest.generated";
import type { UpdateRolePermissionRequest } from "../types/UpdateRolePermissionRequest.generated";
import { RolePermissionField } from "./RolePermissionField.generated";

export type RolePermissionFormValue = CreateRolePermissionRequest | UpdateRolePermissionRequest;

export interface RolePermissionFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface RolePermissionFormProps<TValue extends RolePermissionFormValue = RolePermissionFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly RolePermissionFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function RolePermissionForm<TValue extends RolePermissionFormValue>(props: RolePermissionFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <RolePermissionField
        id="rolepermission-permissionid"
        label="Permission Id"
        kind="text"
        value={props.value["permissionId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["permissionId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["permissionId"]: nextValue as TValue["permissionId"],
          });
        }}
      />
      <RolePermissionField
        id="rolepermission-roleid"
        label="Role Id"
        kind="text"
        value={props.value["roleId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["roleId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["roleId"]: nextValue as TValue["roleId"],
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
