// ------------------------------------------------------------------------------
// GENERATED FILE - source: documents/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { DocumentDto } from "../types/DocumentDto.generated";
import type { CreateDocumentRequest } from "../types/CreateDocumentRequest.generated";
import type { UpdateDocumentRequest } from "../types/UpdateDocumentRequest.generated";
import { DocumentForm } from "../components/DocumentForm.generated";
import { DocumentTable } from "../components/DocumentTable.generated";
import { useDocumentControllerListQuery } from "../../operations/useDocumentControllerListQuery.react-query.generated";
import { useDocumentControllerCreateMutation } from "../../operations/useDocumentControllerCreateMutation.react-mutation.generated";
import { useDocumentControllerUpdateMutation } from "../../operations/useDocumentControllerUpdateMutation.react-mutation.generated";
import { useDocumentControllerDeleteMutation } from "../../operations/useDocumentControllerDeleteMutation.react-mutation.generated";
import { useDocumentControllerSuggestQuery } from "../../operations/useDocumentControllerSuggestQuery.react-query.generated";
import { useDocumentControllerOptionsQuery } from "../../operations/useDocumentControllerOptionsQuery.react-query.generated";
import type { ListDocumentRequest } from "../types/ListDocumentRequest.generated";

export function DocumentsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Documents</h1>
      </header>
      <TabView>
        <TabPanel header="Documents">
          <DocumentSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type DocumentEditorState =
  | { readonly mode: "create"; readonly value: CreateDocumentRequest }
  | { readonly mode: "edit"; readonly item: DocumentDto; readonly value: UpdateDocumentRequest }
  | null;

function DocumentSection() {
  const [listRequest, setListRequest] = useState<ListDocumentRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<DocumentDto | null>(null);
  const list = useDocumentControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useDocumentControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const StateOptions = useDocumentControllerOptionsQuery({ field: "state" });
  const optionItems = {
    state: StateOptions.data ?? [],
  };
  const createMutation = useDocumentControllerCreateMutation();
  const updateMutation = useDocumentControllerUpdateMutation();
  const deleteMutation = useDocumentControllerDeleteMutation();
  const [editor, setEditor] = useState<DocumentEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { currentRevisionNumber: 0, displayName: "", isRevoked: false, mediaType: "", sourceKind: "", state: "", workspaceId: "" } });
  };
  const openEdit = (item: DocumentDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { currentRevisionNumber: item["currentRevisionNumber"], displayName: item["displayName"], isRevoked: item["isRevoked"], mediaType: item["mediaType"], sourceKind: item["sourceKind"], state: item["state"], workspaceId: item["workspaceId"] } });
  };
  const openDetail = (item: DocumentDto) => {
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

  const deleteItem = (item: DocumentDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Documents</h2>
        <Button type="button" label="Create Document" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Documents." />
      ) : null}
      <DocumentTable
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
            <h3>Document details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Current Revision Number</dt>
              <dd>{formatDetailValue(detail["currentRevisionNumber"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Display Name</dt>
              <dd>{formatDetailValue(detail["displayName"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Is Revoked</dt>
              <dd>{formatDetailValue(detail["isRevoked"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Media Type</dt>
              <dd>{formatDetailValue(detail["mediaType"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Source Kind</dt>
              <dd>{formatDetailValue(detail["sourceKind"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>State</dt>
              <dd>{formatDetailValue(detail["state"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Workspace Id</dt>
              <dd>{formatDetailValue(detail["workspaceId"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit Document" : "Create Document"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <DocumentForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateDocumentRequest }
                  : { ...editor, value: value as UpdateDocumentRequest },
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

