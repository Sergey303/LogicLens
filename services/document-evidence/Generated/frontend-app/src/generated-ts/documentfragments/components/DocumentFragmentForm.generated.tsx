// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { Button } from "primereact/button";
import type { CreateDocumentFragmentRequest } from "../types/CreateDocumentFragmentRequest.generated";
import type { UpdateDocumentFragmentRequest } from "../types/UpdateDocumentFragmentRequest.generated";
import { DocumentFragmentField } from "./DocumentFragmentField.generated";

export type DocumentFragmentFormValue = CreateDocumentFragmentRequest | UpdateDocumentFragmentRequest;

export interface DocumentFragmentFormLookupOption {
  readonly label: string;
  readonly value: string;
}

export interface DocumentFragmentFormProps<TValue extends DocumentFragmentFormValue = DocumentFragmentFormValue> {
  readonly value: TValue;
  readonly onChange: (value: TValue) => void;
  readonly onSubmit: () => void;
  readonly submitLabel?: string;
  readonly submitting?: boolean;
  readonly disabled?: boolean;
  readonly errors?: Partial<Record<keyof TValue, string>>;
  readonly lookupOptions?: Readonly<Record<string, readonly DocumentFragmentFormLookupOption[]>>;
  readonly onLookupSuggest?: (field: string, query: string) => void;
}

export function DocumentFragmentForm<TValue extends DocumentFragmentFormValue>(props: DocumentFragmentFormProps<TValue>) {
  const disabled = Boolean(props.disabled || props.submitting);

  return (
    <form
      className="appforge-generated-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit();
      }}
    >
      <DocumentFragmentField
        id="documentfragment-anchorjson"
        label="Anchor Json"
        kind="text"
        value={props.value["anchorJson"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["anchorJson"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["anchorJson"]: nextValue as TValue["anchorJson"],
          });
        }}
      />
      <DocumentFragmentField
        id="documentfragment-contenthash"
        label="Content Hash"
        kind="text"
        value={props.value["contentHash"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["contentHash"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["contentHash"]: nextValue as TValue["contentHash"],
          });
        }}
      />
      <DocumentFragmentField
        id="documentfragment-documentrevisionid"
        label="Document Revision Id"
        kind="text"
        value={props.value["documentRevisionId"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["documentRevisionId"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["documentRevisionId"]: nextValue as TValue["documentRevisionId"],
          });
        }}
      />
      <DocumentFragmentField
        id="documentfragment-kind"
        label="Kind"
        kind="text"
        value={props.value["kind"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["kind"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["kind"]: nextValue as TValue["kind"],
          });
        }}
      />
      <DocumentFragmentField
        id="documentfragment-sequence"
        label="Sequence"
        kind="number"
        value={props.value["sequence"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["sequence"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["sequence"]: nextValue as TValue["sequence"],
          });
        }}
      />
      <DocumentFragmentField
        id="documentfragment-text"
        label="Text"
        kind="text"
        value={props.value["text"]}
        required={true}
        disabled={disabled}
        error={props.errors?.["text"] ?? null}
        onChange={(nextValue) => {
          props.onChange({
            ...props.value,
            ["text"]: nextValue as TValue["text"],
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
