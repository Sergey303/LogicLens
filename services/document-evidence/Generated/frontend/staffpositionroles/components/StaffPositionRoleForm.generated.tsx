// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateStaffPositionRoleRequest } from "../types/CreateStaffPositionRoleRequest.generated";
import type { UpdateStaffPositionRoleRequest } from "../types/UpdateStaffPositionRoleRequest.generated";
import { StaffPositionRoleField } from "./StaffPositionRoleField.generated";

export type StaffPositionRoleFormValue = CreateStaffPositionRoleRequest | UpdateStaffPositionRoleRequest;

export interface StaffPositionRoleFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface StaffPositionRoleFormProps<TValue extends StaffPositionRoleFormValue = StaffPositionRoleFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly StaffPositionRoleFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function StaffPositionRoleForm<TValue extends StaffPositionRoleFormValue>(props: StaffPositionRoleFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <StaffPositionRoleField
        id="staffpositionrole-roleid"
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
      <StaffPositionRoleField
        id="staffpositionrole-staffpositionid"
        label="Staff Position Id"
        kind="text"
        value={props.value["staffPositionId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["staffPositionId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["staffPositionId"]: nextValue as TValue["staffPositionId"],
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
