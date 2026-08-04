// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateDocumentRequest } from "../types/CreateDocumentRequest.generated";
import type { UpdateDocumentRequest } from "../types/UpdateDocumentRequest.generated";
import { DocumentField } from "./DocumentField.generated";

export type DocumentFormValue = CreateDocumentRequest | UpdateDocumentRequest;

export interface DocumentFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface DocumentFormProps<TValue extends DocumentFormValue = DocumentFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly DocumentFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function DocumentForm<TValue extends DocumentFormValue>(props: DocumentFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <DocumentField
        id="document-currentrevisionnumber"
        label="Current Revision Number"
        kind="number"
        value={props.value["currentRevisionNumber"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["currentRevisionNumber"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["currentRevisionNumber"]: nextValue as TValue["currentRevisionNumber"],
          });
        }}
      />
      <DocumentField
        id="document-displayname"
        label="Display Name"
        kind="text"
        value={props.value["displayName"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["displayName"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["displayName"]: nextValue as TValue["displayName"],
          });
        }}
      />
      <DocumentField
        id="document-isrevoked"
        label="Is Revoked"
        kind="boolean"
        value={props.value["isRevoked"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["isRevoked"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["isRevoked"]: nextValue as TValue["isRevoked"],
          });
        }}
      />
      <DocumentField
        id="document-mediatype"
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
      <DocumentField
        id="document-sourcekind"
        label="Source Kind"
        kind="text"
        value={props.value["sourceKind"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["sourceKind"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["sourceKind"]: nextValue as TValue["sourceKind"],
          });
        }}
      />
      <DocumentField
        id="document-state"
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
      <DocumentField
        id="document-workspaceid"
        label="Workspace Id"
        kind="text"
        value={props.value["workspaceId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["workspaceId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["workspaceId"]: nextValue as TValue["workspaceId"],
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
