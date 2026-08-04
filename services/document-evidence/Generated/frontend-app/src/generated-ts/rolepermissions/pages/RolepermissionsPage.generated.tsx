// ------------------------------------------------------------------------------
// GENERATED FILE - source: rolepermissions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { RolePermissionDto } from "../types/RolePermissionDto.generated";
import type { CreateRolePermissionRequest } from "../types/CreateRolePermissionRequest.generated";
import type { UpdateRolePermissionRequest } from "../types/UpdateRolePermissionRequest.generated";
import { RolePermissionForm } from "../components/RolePermissionForm.generated";
import { RolePermissionTable } from "../components/RolePermissionTable.generated";
import { useRolePermissionControllerListQuery } from "../../operations/useRolePermissionControllerListQuery.react-query.generated";
import { useRolePermissionControllerCreateMutation } from "../../operations/useRolePermissionControllerCreateMutation.react-mutation.generated";
import { useRolePermissionControllerUpdateMutation } from "../../operations/useRolePermissionControllerUpdateMutation.react-mutation.generated";
import { useRolePermissionControllerDeleteMutation } from "../../operations/useRolePermissionControllerDeleteMutation.react-mutation.generated";
import { useRolePermissionControllerSuggestQuery } from "../../operations/useRolePermissionControllerSuggestQuery.react-query.generated";
import type { ListRolePermissionRequest } from "../types/ListRolePermissionRequest.generated";

export function RolepermissionsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Rolepermissions</h1>
      </header>
      <TabView>
        <TabPanel header="Role Permissions">
          <RolePermissionSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type RolePermissionEditorState =
  | { readonly mode: "create"; readonly value: CreateRolePermissionRequest }
  | { readonly mode: "edit"; readonly item: RolePermissionDto; readonly value: UpdateRolePermissionRequest }
  | null;

function RolePermissionSection() {
  const [listRequest, setListRequest] = useState<ListRolePermissionRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<RolePermissionDto | null>(null);
  const list = useRolePermissionControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useRolePermissionControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const createMutation = useRolePermissionControllerCreateMutation();
  const updateMutation = useRolePermissionControllerUpdateMutation();
  const deleteMutation = useRolePermissionControllerDeleteMutation();
  const [editor, setEditor] = useState<RolePermissionEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { permissionId: "", roleId: "" } });
  };
  const openEdit = (item: RolePermissionDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { permissionId: item["permissionId"], roleId: item["roleId"] } });
  };
  const openDetail = (item: RolePermissionDto) => {
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

  const deleteItem = (item: RolePermissionDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Role Permissions</h2>
        <Button type="button" label="Create RolePermission" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Role Permissions." />
      ) : null}
      <RolePermissionTable
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
            <h3>Role Permission details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Permission Id</dt>
              <dd>{formatDetailValue(detail["permissionId"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Role Id</dt>
              <dd>{formatDetailValue(detail["roleId"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit RolePermission" : "Create RolePermission"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <RolePermissionForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateRolePermissionRequest }
                  : { ...editor, value: value as UpdateRolePermissionRequest },
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

