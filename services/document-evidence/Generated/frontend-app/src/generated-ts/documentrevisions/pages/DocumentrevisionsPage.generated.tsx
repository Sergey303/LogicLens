// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentrevisions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { DocumentRevisionDto } from "../types/DocumentRevisionDto.generated";
import type { CreateDocumentRevisionRequest } from "../types/CreateDocumentRevisionRequest.generated";
import type { UpdateDocumentRevisionRequest } from "../types/UpdateDocumentRevisionRequest.generated";
import { DocumentRevisionForm } from "../components/DocumentRevisionForm.generated";
import { DocumentRevisionTable } from "../components/DocumentRevisionTable.generated";
import { useDocumentRevisionControllerListQuery } from "../../operations/useDocumentRevisionControllerListQuery.react-query.generated";
import { useDocumentRevisionControllerCreateMutation } from "../../operations/useDocumentRevisionControllerCreateMutation.react-mutation.generated";
import { useDocumentRevisionControllerUpdateMutation } from "../../operations/useDocumentRevisionControllerUpdateMutation.react-mutation.generated";
import { useDocumentRevisionControllerDeleteMutation } from "../../operations/useDocumentRevisionControllerDeleteMutation.react-mutation.generated";
import { useDocumentRevisionControllerSuggestQuery } from "../../operations/useDocumentRevisionControllerSuggestQuery.react-query.generated";
import { useDocumentRevisionControllerOptionsQuery } from "../../operations/useDocumentRevisionControllerOptionsQuery.react-query.generated";
import type { ListDocumentRevisionRequest } from "../types/ListDocumentRevisionRequest.generated";

export function DocumentrevisionsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Documentrevisions</h1>
      </header>
      <TabView>
        <TabPanel header="Document Revisions">
          <DocumentRevisionSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type DocumentRevisionEditorState =
  | { readonly mode: "create"; readonly value: CreateDocumentRevisionRequest }
  | { readonly mode: "edit"; readonly item: DocumentRevisionDto; readonly value: UpdateDocumentRevisionRequest }
  | null;

function DocumentRevisionSection() {
  const [listRequest, setListRequest] = useState<ListDocumentRevisionRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<DocumentRevisionDto | null>(null);
  const list = useDocumentRevisionControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useDocumentRevisionControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const StateOptions = useDocumentRevisionControllerOptionsQuery({ field: "state" });
  const optionItems = {
    state: StateOptions.data ?? [],
  };
  const createMutation = useDocumentRevisionControllerCreateMutation();
  const updateMutation = useDocumentRevisionControllerUpdateMutation();
  const deleteMutation = useDocumentRevisionControllerDeleteMutation();
  const [editor, setEditor] = useState<DocumentRevisionEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { adapter: null, adapterVersion: null, documentId: "", manifestHash: null, revisionNumber: 0, state: "", storedObjectId: "" } });
  };
  const openEdit = (item: DocumentRevisionDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { adapter: item["adapter"], adapterVersion: item["adapterVersion"], documentId: item["documentId"], manifestHash: item["manifestHash"], revisionNumber: item["revisionNumber"], state: item["state"], storedObjectId: item["storedObjectId"] } });
  };
  const openDetail = (item: DocumentRevisionDto) => {
    setDetail(item);
  };

  const closeEditor = () => {
    resetEditorErrors();
    setEditor(null);
  };

  const saveEditor = () => {
    if (editor === null) {
      return;
    }

    if (editor.mode === "create") {
      void createMutation.execute(editor.value)
        .then(() => closeEditor())
        .catch(() => undefined);
      return;
    }

    void updateMutation.execute({
      id: editor.item["id"],
      body: editor.value,
    })
      .then(() => closeEditor())
      .catch(() => undefined);
  };

  const deleteItem = (item: DocumentRevisionDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Document Revisions</h2>
        <Button type="button" label="Create DocumentRevision" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Document Revisions." />
      ) : null}
      <DocumentRevisionTable
        items={items}
        loading={list.isLoading}
        lazy
        page={listRequest.page}
        pageSize={listRequest.pageSize}
        totalRecords={totalCount}
        suggestions={suggestionItems}
        onSuggest={(field, query) => setSuggestRequest({ field, query })}
        options={optionItems}
        onPageChange={(next) => setListRequest((current) => ({
          ...current,
          page: next.page,
          pageSize: next.pageSize,
        }))}
        onSortChange={(sort) => setListRequest((current) => ({
          ...current,
          page: 1,
          sort: sort.map((item) => ({ field: item.field, direction: item.direction })),
        }))}
        onFilterChange={(filters) => setListRequest((current) => ({
          ...current,
          page: 1,
          filters: filters.map((item) => ({
            field: item.field,
            operator: item.operator,
            value: item.value,
            values: [...item.values],
          })),
        }))}
        onOpen={openDetail}
        onEdit={openEdit}
        onDelete={deleteItem}
      />
      {detail ? (
        <section className="appforge-generated-detail-panel">
          <div className="appforge-generated-detail-header">
            <h3>Document Revision details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Adapter</dt>
              <dd>{formatDetailValue(detail["adapter"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Adapter Version</dt>
              <dd>{formatDetailValue(detail["adapterVersion"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Document Id</dt>
              <dd>{formatDetailValue(detail["documentId"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Manifest Hash</dt>
              <dd>{formatDetailValue(detail["manifestHash"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Revision Number</dt>
              <dd>{formatDetailValue(detail["revisionNumber"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>State</dt>
              <dd>{formatDetailValue(detail["state"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Stored Object Id</dt>
              <dd>{formatDetailValue(detail["storedObjectId"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit DocumentRevision" : "Create DocumentRevision"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <DocumentRevisionForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateDocumentRevisionRequest }
                  : { ...editor, value: value as UpdateDocumentRevisionRequest },
              );
            }}
            onSubmit={saveEditor}
            submitLabel={editor.mode === "edit" ? "Save" : "Create"}
            submitting={saving}
            errors={readFieldErrors(editor.mode === "edit" ? updateMutation.error : createMutation.error)}
          />
        ) : null}
      </Dialog>
    </section>
  );
}


function formatDetailValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}

