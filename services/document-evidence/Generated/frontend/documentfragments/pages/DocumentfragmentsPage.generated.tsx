// ------------------------------------------------------------------------------
// GENERATED FILE - source: documentfragments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { DocumentFragmentDto } from "../types/DocumentFragmentDto.generated";
import type { CreateDocumentFragmentRequest } from "../types/CreateDocumentFragmentRequest.generated";
import type { UpdateDocumentFragmentRequest } from "../types/UpdateDocumentFragmentRequest.generated";
import { DocumentFragmentForm } from "../components/DocumentFragmentForm.generated";
import { DocumentFragmentTable } from "../components/DocumentFragmentTable.generated";
import { useDocumentFragmentControllerListQuery } from "../../operations/useDocumentFragmentControllerListQuery.react-query.generated";
import { useDocumentFragmentControllerCreateMutation } from "../../operations/useDocumentFragmentControllerCreateMutation.react-mutation.generated";
import { useDocumentFragmentControllerUpdateMutation } from "../../operations/useDocumentFragmentControllerUpdateMutation.react-mutation.generated";
import { useDocumentFragmentControllerDeleteMutation } from "../../operations/useDocumentFragmentControllerDeleteMutation.react-mutation.generated";
import { useDocumentFragmentControllerSuggestQuery } from "../../operations/useDocumentFragmentControllerSuggestQuery.react-query.generated";
import { useDocumentFragmentControllerOptionsQuery } from "../../operations/useDocumentFragmentControllerOptionsQuery.react-query.generated";
import type { ListDocumentFragmentRequest } from "../types/ListDocumentFragmentRequest.generated";

export function DocumentfragmentsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Documentfragments</h1>
      </header>
      <TabView>
        <TabPanel header="Document Fragments">
          <DocumentFragmentSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type DocumentFragmentEditorState =
  | { readonly mode: "create"; readonly value: CreateDocumentFragmentRequest }
  | { readonly mode: "edit"; readonly item: DocumentFragmentDto; readonly value: UpdateDocumentFragmentRequest }
  | null;

function DocumentFragmentSection() {
  const [listRequest, setListRequest] = useState<ListDocumentFragmentRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<DocumentFragmentDto | null>(null);
  const list = useDocumentFragmentControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useDocumentFragmentControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const KindOptions = useDocumentFragmentControllerOptionsQuery({ field: "kind" });
  const optionItems = {
    kind: KindOptions.data ?? [],
  };
  const createMutation = useDocumentFragmentControllerCreateMutation();
  const updateMutation = useDocumentFragmentControllerUpdateMutation();
  const deleteMutation = useDocumentFragmentControllerDeleteMutation();
  const [editor, setEditor] = useState<DocumentFragmentEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { anchorJson: "", contentHash: "", documentRevisionId: "", kind: "", sequence: 0, text: "" } });
  };
  const openEdit = (item: DocumentFragmentDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { anchorJson: item["anchorJson"], contentHash: item["contentHash"], documentRevisionId: item["documentRevisionId"], kind: item["kind"], sequence: item["sequence"], text: item["text"] } });
  };
  const openDetail = (item: DocumentFragmentDto) => {
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

  const deleteItem = (item: DocumentFragmentDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Document Fragments</h2>
        <Button type="button" label="Create DocumentFragment" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Document Fragments." />
      ) : null}
      <DocumentFragmentTable
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
            <h3>Document Fragment details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Anchor Json</dt>
              <dd>{formatDetailValue(detail["anchorJson"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Content Hash</dt>
              <dd>{formatDetailValue(detail["contentHash"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Document Revision Id</dt>
              <dd>{formatDetailValue(detail["documentRevisionId"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Kind</dt>
              <dd>{formatDetailValue(detail["kind"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Sequence</dt>
              <dd>{formatDetailValue(detail["sequence"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Text</dt>
              <dd>{formatDetailValue(detail["text"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit DocumentFragment" : "Create DocumentFragment"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <DocumentFragmentForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateDocumentFragmentRequest }
                  : { ...editor, value: value as UpdateDocumentFragmentRequest },
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

