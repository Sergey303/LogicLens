// ------------------------------------------------------------------------------
// GENERATED FILE - source: roles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { RoleDto } from "../types/RoleDto.generated";
import type { CreateRoleRequest } from "../types/CreateRoleRequest.generated";
import type { UpdateRoleRequest } from "../types/UpdateRoleRequest.generated";
import { RoleForm } from "../components/RoleForm.generated";
import { RoleTable } from "../components/RoleTable.generated";
import { useRoleControllerListQuery } from "../../operations/useRoleControllerListQuery.react-query.generated";
import { useRoleControllerCreateMutation } from "../../operations/useRoleControllerCreateMutation.react-mutation.generated";
import { useRoleControllerUpdateMutation } from "../../operations/useRoleControllerUpdateMutation.react-mutation.generated";
import { useRoleControllerDeleteMutation } from "../../operations/useRoleControllerDeleteMutation.react-mutation.generated";
import { useRoleControllerSuggestQuery } from "../../operations/useRoleControllerSuggestQuery.react-query.generated";
import type { ListRoleRequest } from "../types/ListRoleRequest.generated";

export function RolesPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Roles</h1>
      </header>
      <TabView>
        <TabPanel header="Roles">
          <RoleSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type RoleEditorState =
  | { readonly mode: "create"; readonly value: CreateRoleRequest }
  | { readonly mode: "edit"; readonly item: RoleDto; readonly value: UpdateRoleRequest }
  | null;

function RoleSection() {
  const [listRequest, setListRequest] = useState<ListRoleRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<RoleDto | null>(null);
  const list = useRoleControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useRoleControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const createMutation = useRoleControllerCreateMutation();
  const updateMutation = useRoleControllerUpdateMutation();
  const deleteMutation = useRoleControllerDeleteMutation();
  const [editor, setEditor] = useState<RoleEditorState>(null);
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
  const openEdit = (item: RoleDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { code: item["code"], name: item["name"] } });
  };
  const openDetail = (item: RoleDto) => {
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

  const deleteItem = (item: RoleDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Roles</h2>
        <Button type="button" label="Create Role" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Roles." />
      ) : null}
      <RoleTable
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
            <h3>Role details</h3>
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
        header={editor?.mode === "edit" ? "Edit Role" : "Create Role"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <RoleForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateRoleRequest }
                  : { ...editor, value: value as UpdateRoleRequest },
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

