// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionassignments/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { StaffPositionAssignmentDto } from "../types/StaffPositionAssignmentDto.generated";
import type { CreateStaffPositionAssignmentRequest } from "../types/CreateStaffPositionAssignmentRequest.generated";
import type { UpdateStaffPositionAssignmentRequest } from "../types/UpdateStaffPositionAssignmentRequest.generated";
import { StaffPositionAssignmentForm } from "../components/StaffPositionAssignmentForm.generated";
import { StaffPositionAssignmentTable } from "../components/StaffPositionAssignmentTable.generated";
import { useStaffPositionAssignmentControllerListQuery } from "../../operations/useStaffPositionAssignmentControllerListQuery.react-query.generated";
import { useStaffPositionAssignmentControllerCreateMutation } from "../../operations/useStaffPositionAssignmentControllerCreateMutation.react-mutation.generated";
import { useStaffPositionAssignmentControllerUpdateMutation } from "../../operations/useStaffPositionAssignmentControllerUpdateMutation.react-mutation.generated";
import { useStaffPositionAssignmentControllerDeleteMutation } from "../../operations/useStaffPositionAssignmentControllerDeleteMutation.react-mutation.generated";
import { useStaffPositionAssignmentControllerSuggestQuery } from "../../operations/useStaffPositionAssignmentControllerSuggestQuery.react-query.generated";
import type { ListStaffPositionAssignmentRequest } from "../types/ListStaffPositionAssignmentRequest.generated";

export function StaffpositionassignmentsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Staffpositionassignments</h1>
      </header>
      <TabView>
        <TabPanel header="Staff Position Assignments">
          <StaffPositionAssignmentSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type StaffPositionAssignmentEditorState =
  | { readonly mode: "create"; readonly value: CreateStaffPositionAssignmentRequest }
  | { readonly mode: "edit"; readonly item: StaffPositionAssignmentDto; readonly value: UpdateStaffPositionAssignmentRequest }
  | null;

function StaffPositionAssignmentSection() {
  const [listRequest, setListRequest] = useState<ListStaffPositionAssignmentRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<StaffPositionAssignmentDto | null>(null);
  const list = useStaffPositionAssignmentControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useStaffPositionAssignmentControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const createMutation = useStaffPositionAssignmentControllerCreateMutation();
  const updateMutation = useStaffPositionAssignmentControllerUpdateMutation();
  const deleteMutation = useStaffPositionAssignmentControllerDeleteMutation();
  const [editor, setEditor] = useState<StaffPositionAssignmentEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { assignmentKind: "", endsAt: null, endsAtUtc: null, isActive: false, reason: null, staffPositionId: "", startsAt: "", startsAtUtc: "", userId: "" } });
  };
  const openEdit = (item: StaffPositionAssignmentDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { assignmentKind: item["assignmentKind"], endsAt: item["endsAt"], endsAtUtc: item["endsAtUtc"], isActive: item["isActive"], reason: item["reason"], staffPositionId: item["staffPositionId"], startsAt: item["startsAt"], startsAtUtc: item["startsAtUtc"], userId: item["userId"] } });
  };
  const openDetail = (item: StaffPositionAssignmentDto) => {
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

  const deleteItem = (item: StaffPositionAssignmentDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Staff Position Assignments</h2>
        <Button type="button" label="Create StaffPositionAssignment" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Staff Position Assignments." />
      ) : null}
      <StaffPositionAssignmentTable
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
            <h3>Staff Position Assignment details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Assignment Kind</dt>
              <dd>{formatDetailValue(detail["assignmentKind"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Ends At</dt>
              <dd>{formatDetailValue(detail["endsAt"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Ends At Utc</dt>
              <dd>{formatDetailValue(detail["endsAtUtc"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Is Active</dt>
              <dd>{formatDetailValue(detail["isActive"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Reason</dt>
              <dd>{formatDetailValue(detail["reason"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Staff Position Id</dt>
              <dd>{formatDetailValue(detail["staffPositionId"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Starts At</dt>
              <dd>{formatDetailValue(detail["startsAt"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Starts At Utc</dt>
              <dd>{formatDetailValue(detail["startsAtUtc"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>User Id</dt>
              <dd>{formatDetailValue(detail["userId"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit StaffPositionAssignment" : "Create StaffPositionAssignment"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <StaffPositionAssignmentForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateStaffPositionAssignmentRequest }
                  : { ...editor, value: value as UpdateStaffPositionAssignmentRequest },
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

