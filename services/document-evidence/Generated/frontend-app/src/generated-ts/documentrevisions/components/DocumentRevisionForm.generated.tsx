// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateDocumentRevisionRequest } from "../types/CreateDocumentRevisionRequest.generated";
import type { UpdateDocumentRevisionRequest } from "../types/UpdateDocumentRevisionRequest.generated";
import { DocumentRevisionField } from "./DocumentRevisionField.generated";

export type DocumentRevisionFormValue = CreateDocumentRevisionRequest | UpdateDocumentRevisionRequest;

export interface DocumentRevisionFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface DocumentRevisionFormProps<TValue extends DocumentRevisionFormValue = DocumentRevisionFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly DocumentRevisionFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function DocumentRevisionForm<TValue extends DocumentRevisionFormValue>(props: DocumentRevisionFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <DocumentRevisionField
        id="documentrevision-adapter"
        label="Adapter"
        kind="text"
        value={props.value["adapter"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["adapter"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["adapter"]: nextValue as TValue["adapter"],
          });
        }}
      />
      <DocumentRevisionField
        id="documentrevision-adapterversion"
        label="Adapter Version"
        kind="text"
        value={props.value["adapterVersion"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["adapterVersion"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["adapterVersion"]: nextValue as TValue["adapterVersion"],
          });
        }}
      />
      <DocumentRevisionField
        id="documentrevision-documentid"
        label="Document Id"
        kind="text"
        value={props.value["documentId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["documentId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["documentId"]: nextValue as TValue["documentId"],
          });
        }}
      />
      <DocumentRevisionField
        id="documentrevision-manifesthash"
        label="Manifest Hash"
        kind="text"
        value={props.value["manifestHash"]}
        required={false}
        disabled={disabled}
        error={props.errors?.["manifestHash"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["manifestHash"]: nextValue as TValue["manifestHash"],
          });
        }}
      />
      <DocumentRevisionField
        id="documentrevision-revisionnumber"
        label="Revision Number"
        kind="number"
        value={props.value["revisionNumber"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["revisionNumber"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["revisionNumber"]: nextValue as TValue["revisionNumber"],
          });
        }}
      />
      <DocumentRevisionField
        id="documentrevision-state"
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
      <DocumentRevisionField
        id="documentrevision-storedobjectid"
        label="Stored Object Id"
        kind="text"
        value={props.value["storedObjectId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["storedObjectId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["storedObjectId"]: nextValue as TValue["storedObjectId"],
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
