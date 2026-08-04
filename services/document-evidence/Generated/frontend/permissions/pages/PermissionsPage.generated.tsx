// ------------------------------------------------------------------------------
// GENERATED FILE - source: permissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { PermissionDto } from "../types/PermissionDto.generated";
import type { CreatePermissionRequest } from "../types/CreatePermissionRequest.generated";
import type { UpdatePermissionRequest } from "../types/UpdatePermissionRequest.generated";
import { PermissionForm } from "../components/PermissionForm.generated";
import { PermissionTable } from "../components/PermissionTable.generated";
import { usePermissionControllerListQuery } from "../../operations/usePermissionControllerListQuery.react-query.generated";
import { usePermissionControllerCreateMutation } from "../../operations/usePermissionControllerCreateMutation.react-mutation.generated";
import { usePermissionControllerUpdateMutation } from "../../operations/usePermissionControllerUpdateMutation.react-mutation.generated";
import { usePermissionControllerDeleteMutation } from "../../operations/usePermissionControllerDeleteMutation.react-mutation.generated";
import { usePermissionControllerSuggestQuery } from "../../operations/usePermissionControllerSuggestQuery.react-query.generated";
import type { ListPermissionRequest } from "../types/ListPermissionRequest.generated";

export function PermissionsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Permissions</h1>
      </header>
      <TabView>
        <TabPanel header="Permissions">
          <PermissionSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type PermissionEditorState =
  | { readonly mode: "create"; readonly value: CreatePermissionRequest }
  | { readonly mode: "edit"; readonly item: PermissionDto; readonly value: UpdatePermissionRequest }
  | null;

function PermissionSection() {
  const [listRequest, setListRequest] = useState<ListPermissionRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<PermissionDto | null>(null);
  const list = usePermissionControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = usePermissionControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const createMutation = usePermissionControllerCreateMutation();
  const updateMutation = usePermissionControllerUpdateMutation();
  const deleteMutation = usePermissionControllerDeleteMutation();
  const [editor, setEditor] = useState<PermissionEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { code: "", name: "" } });
  };
  const openEdit = (item: PermissionDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { code: item["code"], name: item["name"] } });
  };
  const openDetail = (item: PermissionDto) => {
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

  const deleteItem = (item: PermissionDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Permissions</h2>
        <Button type="button" label="Create Permission" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Permissions." />
      ) : null}
      <PermissionTable
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
            <h3>Permission details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Code</dt>
              <dd>{formatDetailValue(detail["code"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Name</dt>
              <dd>{formatDetailValue(detail["name"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit Permission" : "Create Permission"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <PermissionForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreatePermissionRequest }
                  : { ...editor, value: value as UpdatePermissionRequest },
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

