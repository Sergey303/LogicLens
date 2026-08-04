// ------------------------------------------------------------------------------
// GENERATED FILE - source: storedobjects/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { StoredObjectDto } from "../types/StoredObjectDto.generated";
import type { CreateStoredObjectRequest } from "../types/CreateStoredObjectRequest.generated";
import type { UpdateStoredObjectRequest } from "../types/UpdateStoredObjectRequest.generated";
import { StoredObjectForm } from "../components/StoredObjectForm.generated";
import { StoredObjectTable } from "../components/StoredObjectTable.generated";
import { useStoredObjectControllerListQuery } from "../../operations/useStoredObjectControllerListQuery.react-query.generated";
import { useStoredObjectControllerCreateMutation } from "../../operations/useStoredObjectControllerCreateMutation.react-mutation.generated";
import { useStoredObjectControllerUpdateMutation } from "../../operations/useStoredObjectControllerUpdateMutation.react-mutation.generated";
import { useStoredObjectControllerDeleteMutation } from "../../operations/useStoredObjectControllerDeleteMutation.react-mutation.generated";
import { useStoredObjectControllerSuggestQuery } from "../../operations/useStoredObjectControllerSuggestQuery.react-query.generated";
import type { ListStoredObjectRequest } from "../types/ListStoredObjectRequest.generated";

export function StoredobjectsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Storedobjects</h1>
      </header>
      <TabView>
        <TabPanel header="Stored Objects">
          <StoredObjectSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type StoredObjectEditorState =
  | { readonly mode: "create"; readonly value: CreateStoredObjectRequest }
  | { readonly mode: "edit"; readonly item: StoredObjectDto; readonly value: UpdateStoredObjectRequest }
  | null;

function StoredObjectSection() {
  const [listRequest, setListRequest] = useState<ListStoredObjectRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<StoredObjectDto | null>(null);
  const list = useStoredObjectControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useStoredObjectControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const createMutation = useStoredObjectControllerCreateMutation();
  const updateMutation = useStoredObjectControllerUpdateMutation();
  const deleteMutation = useStoredObjectControllerDeleteMutation();
  const [editor, setEditor] = useState<StoredObjectEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { mediaType: "", sha256: "", sizeBytes: 0, storageKey: "" } });
  };
  const openEdit = (item: StoredObjectDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { mediaType: item["mediaType"], sha256: item["sha256"], sizeBytes: item["sizeBytes"], storageKey: item["storageKey"] } });
  };
  const openDetail = (item: StoredObjectDto) => {
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

  const deleteItem = (item: StoredObjectDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Stored Objects</h2>
        <Button type="button" label="Create StoredObject" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Stored Objects." />
      ) : null}
      <StoredObjectTable
        items={items}
        loading={list.isLoading}
        lazy
        page={listRequest.page}
        pageSize={listRequest.pageSize}
        totalRecords={totalCount}
        suggestions={suggestionItems}
        onSuggest={(field, query) => setSuggestRequest({ field, query })}
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
            <h3>Stored Object details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Media Type</dt>
              <dd>{formatDetailValue(detail["mediaType"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Sha256</dt>
              <dd>{formatDetailValue(detail["sha256"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Size Bytes</dt>
              <dd>{formatDetailValue(detail["sizeBytes"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Storage Key</dt>
              <dd>{formatDetailValue(detail["storageKey"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit StoredObject" : "Create StoredObject"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <StoredObjectForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateStoredObjectRequest }
                  : { ...editor, value: value as UpdateStoredObjectRequest },
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

