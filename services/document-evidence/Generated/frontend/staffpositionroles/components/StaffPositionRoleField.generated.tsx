// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Calendar } from "primereact/calendar";
import { Checkbox } from "primereact/checkbox";
import { Dropdown } from "primereact/dropdown";
import { InputNumber } from "primereact/inputnumber";
import { InputText } from "primereact/inputtext";

export type StaffPositionRoleFieldKind = "text" | "number" | "date" | "boolean" | "lookup";

export type StaffPositionRoleFieldValue = string | number | boolean | null | undefined;

export interface StaffPositionRoleFieldLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface StaffPositionRoleFieldProps {
  readonly id: string;
  readonly label: string;
  readonly kind: StaffPositionRoleFieldKind;
  readonly value: StaffPositionRoleFieldValue;
  readonly onChange: (value: StaffPositionRoleFieldValue) => void;
  readonly required?: boolean;
  readonly disabled?: boolean;
  readonly error?: string | null;
  readonly helperText?: string | null;
  readonly lookupOptions?: readonly StaffPositionRoleFieldLookupOption[];
  readonly onLookupFilter?: (query: string) => void;
}

export function StaffPositionRoleField(props: StaffPositionRoleFieldProps) {
  const describedBy = props.error || props.helperText ? `${props.id}-help` : undefined;

  return (
    <div className="appforge-generated-field">
      <label className="appforge-generated-field-label" htmlFor={props.id}>
        {props.label}
        {props.required ? <span aria-hidden="true"> *</span> : null}
      </label>
      {renderInput(props, describedBy)}
      {props.error ? (
        <small id={describedBy} className="p-error">
          {props.error}
        </small>
      ) : null}
      {!props.error && props.helperText ? (
        <small id={describedBy} className="appforge-generated-field-help">
          {props.helperText}
        </small>
      ) : null}
    </div>
  );
}

function renderInput(props: StaffPositionRoleFieldProps, describedBy: string | undefined) {
  if (props.kind === "boolean") {
    return (
      <Checkbox
        inputId={props.id}
        checked={Boolean(props.value)}
        disabled={props.disabled}
        aria-describedby={describedBy}
        onChange={(event) => props.onChange(Boolean(event.checked))}
      />
    );
  }

  if (props.kind === "number") {
    return (
      <InputNumber
        inputId={props.id}
        value={typeof props.value === "number" ? props.value : null}
        disabled={props.disabled}
        aria-describedby={describedBy}
        onValueChange={(event) => props.onChange(event.value ?? null)}
      />
    );
  }

  if (props.kind === "date") {
    return (
      <Calendar
        inputId={props.id}
        value={toCalendarValue(props.value)}
        disabled={props.disabled}
        aria-describedby={describedBy}
        invalid={Boolean(props.error)}
        showIcon
        onChange={(event) => props.onChange(toDateOnlyValue(event.value))}
      />
    );
  }

  if (props.kind === "lookup") {
    return (
      <Dropdown
        inputId={props.id}
        value={typeof props.value === "string" ? props.value : null}
        options={[...(props.lookupOptions ?? [])]}
        optionLabel="label"
        optionValue="value"
        disabled={props.disabled}
        aria-describedby={describedBy}
        invalid={Boolean(props.error)}
        filter
        showClear={!props.required}
        onFilter={(event: { readonly filter?: string }) => props.onLookupFilter?.(String(event.filter ?? ""))}
        onChange={(event: { readonly value?: unknown }) => props.onChange(readLookupValue(event.value))}
      />
    );
  }

  return (
    <InputText
      id={props.id}
      value={typeof props.value === "string" ? props.value : ""}
      disabled={props.disabled}
      aria-describedby={describedBy}
      invalid={Boolean(props.error)}
      onChange={(event) => props.onChange(event.target.value)}
    />
  );
}

function readLookupValue(value: unknown) {
  if (typeof value === "string" && value.length > 0) {
    return value;
  }

  return null;
}

function toCalendarValue(value: StaffPositionRoleFieldValue) {
  if (typeof value !== "string" || value.length === 0) {
    return null;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function toDateOnlyValue(value: unknown) {
  if (!(value instanceof Date)) {
    return null;
  }

  return value.toISOString().slice(0, 10);
}
