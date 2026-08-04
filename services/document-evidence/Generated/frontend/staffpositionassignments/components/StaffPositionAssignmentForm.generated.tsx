// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateStaffPositionAssignmentRequest } from "../types/CreateStaffPositionAssignmentRequest.generated";
import type { UpdateStaffPositionAssignmentRequest } from "../types/UpdateStaffPositionAssignmentRequest.generated";
import { StaffPositionAssignmentField } from "./StaffPositionAssignmentField.generated";

export type StaffPositionAssignmentFormValue = CreateStaffPositionAssignmentRequest | UpdateStaffPositionAssignmentRequest;

export interface StaffPositionAssignmentFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface StaffPositionAssignmentFormProps<TValue extends StaffPositionAssignmentFormValue = StaffPositionAssignmentFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly StaffPositionAssignmentFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function StaffPositionAssignmentForm<TValue extends StaffPositionAssignmentFormValue>(props: StaffPositionAssignmentFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <StaffPositionAssignmentField
        id="staffpositionassignment-assignmentkind"
        label="Assignment Kind"
        kind="text"
        value={props.value["assignmentKind"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["assignmentKind"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["assignmentKind"]: nextValue as TValue["assignmentKind"],
          });
        }}
      />
      <StaffPositionAssignmentField
        id="staffpositionassignment-endsat"
        label="Ends At"
        kind="date"
        value={props.value["endsAt"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["endsAt"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["endsAt"]: nextValue as TValue["endsAt"],
          });
        }}
      />
      <StaffPositionAssignmentField
        id="staffpositionassignment-endsatutc"
        label="Ends At Utc"
        kind="date"
        value={props.value["endsAtUtc"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["endsAtUtc"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["endsAtUtc"]: nextValue as TValue["endsAtUtc"],
          });
        }}
      />
      <StaffPositionAssignmentField
        id="staffpositionassignment-isactive"
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
      <StaffPositionAssignmentField
        id="staffpositionassignment-reason"
        label="Reason"
        kind="text"
        value={props.value["reason"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["reason"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["reason"]: nextValue as TValue["reason"],
          });
        }}
      />
      <StaffPositionAssignmentField
        id="staffpositionassignment-staffpositionid"
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
      <StaffPositionAssignmentField
        id="staffpositionassignment-startsat"
        label="Starts At"
        kind="date"
        value={props.value["startsAt"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["startsAt"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["startsAt"]: nextValue as TValue["startsAt"],
          });
        }}
      />
      <StaffPositionAssignmentField
        id="staffpositionassignment-startsatutc"
        label="Starts At Utc"
        kind="date"
        value={props.value["startsAtUtc"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["startsAtUtc"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["startsAtUtc"]: nextValue as TValue["startsAtUtc"],
          });
        }}
      />
      <StaffPositionAssignmentField
        id="staffpositionassignment-userid"
        label="User Id"
        kind="text"
        value={props.value["userId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["userId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["userId"]: nextValue as TValue["userId"],
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
