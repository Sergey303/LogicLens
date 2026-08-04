// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { StaffPositionRoleDto } from "../types/StaffPositionRoleDto.generated";
import type { CreateStaffPositionRoleRequest } from "../types/CreateStaffPositionRoleRequest.generated";
import type { UpdateStaffPositionRoleRequest } from "../types/UpdateStaffPositionRoleRequest.generated";
import { StaffPositionRoleForm } from "../components/StaffPositionRoleForm.generated";
import { StaffPositionRoleTable } from "../components/StaffPositionRoleTable.generated";
import { useStaffPositionRoleControllerListQuery } from "../../operations/useStaffPositionRoleControllerListQuery.react-query.generated";
import { useStaffPositionRoleControllerCreateMutation } from "../../operations/useStaffPositionRoleControllerCreateMutation.react-mutation.generated";
import { useStaffPositionRoleControllerUpdateMutation } from "../../operations/useStaffPositionRoleControllerUpdateMutation.react-mutation.generated";
import { useStaffPositionRoleControllerDeleteMutation } from "../../operations/useStaffPositionRoleControllerDeleteMutation.react-mutation.generated";
import { useStaffPositionRoleControllerSuggestQuery } from "../../operations/useStaffPositionRoleControllerSuggestQuery.react-query.generated";
import type { ListStaffPositionRoleRequest } from "../types/ListStaffPositionRoleRequest.generated";

export function StaffpositionrolesPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Staffpositionroles</h1>
      </header>
      <TabView>
        <TabPanel header="Staff Position Roles">
          <StaffPositionRoleSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type StaffPositionRoleEditorState =
  | { readonly mode: "create"; readonly value: CreateStaffPositionRoleRequest }
  | { readonly mode: "edit"; readonly item: StaffPositionRoleDto; readonly value: UpdateStaffPositionRoleRequest }
  | null;

function StaffPositionRoleSection() {
  const [listRequest, setListRequest] = useState<ListStaffPositionRoleRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<StaffPositionRoleDto | null>(null);
  const list = useStaffPositionRoleControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useStaffPositionRoleControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const createMutation = useStaffPositionRoleControllerCreateMutation();
  const updateMutation = useStaffPositionRoleControllerUpdateMutation();
  const deleteMutation = useStaffPositionRoleControllerDeleteMutation();
  const [editor, setEditor] = useState<StaffPositionRoleEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { roleId: "", staffPositionId: "" } });
  };
  const openEdit = (item: StaffPositionRoleDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { roleId: item["roleId"], staffPositionId: item["staffPositionId"] } });
  };
  const openDetail = (item: StaffPositionRoleDto) => {
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

  const deleteItem = (item: StaffPositionRoleDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Staff Position Roles</h2>
        <Button type="button" label="Create StaffPositionRole" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Staff Position Roles." />
      ) : null}
      <StaffPositionRoleTable
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
            <h3>Staff Position Role details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Role Id</dt>
              <dd>{formatDetailValue(detail["roleId"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Staff Position Id</dt>
              <dd>{formatDetailValue(detail["staffPositionId"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit StaffPositionRole" : "Create StaffPositionRole"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <StaffPositionRoleForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateStaffPositionRoleRequest }
                  : { ...editor, value: value as UpdateStaffPositionRoleRequest },
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

