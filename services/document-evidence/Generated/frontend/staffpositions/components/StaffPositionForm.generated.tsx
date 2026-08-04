// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateStaffPositionRequest } from "../types/CreateStaffPositionRequest.generated";
import type { UpdateStaffPositionRequest } from "../types/UpdateStaffPositionRequest.generated";
import { StaffPositionField } from "./StaffPositionField.generated";

export type StaffPositionFormValue = CreateStaffPositionRequest | UpdateStaffPositionRequest;

export interface StaffPositionFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface StaffPositionFormProps<TValue extends StaffPositionFormValue = StaffPositionFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly StaffPositionFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function StaffPositionForm<TValue extends StaffPositionFormValue>(props: StaffPositionFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <StaffPositionField
        id="staffposition-code"
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
      <StaffPositionField
        id="staffposition-description"
        label="Description"
        kind="text"
        value={props.value["description"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["description"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["description"]: nextValue as TValue["description"],
          });
        }}
      />
      <StaffPositionField
        id="staffposition-isactive"
        label="Is Active"
        kind="boolean"
        value={props.value["isActive"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["isActive"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["isActive"]: nextValue as TValue["isActive"],
          });
        }}
      />
      <StaffPositionField
        id="staffposition-name"
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
      <StaffPositionField
        id="staffposition-parentpositionid"
        label="Parent Position Id"
        kind="text"
        value={props.value["parentPositionId"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["parentPositionId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["parentPositionId"]: nextValue as TValue["parentPositionId"],
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
