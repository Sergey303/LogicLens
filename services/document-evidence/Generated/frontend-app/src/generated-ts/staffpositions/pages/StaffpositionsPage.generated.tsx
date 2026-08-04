// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositions/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { StaffPositionDto } from "../types/StaffPositionDto.generated";
import type { CreateStaffPositionRequest } from "../types/CreateStaffPositionRequest.generated";
import type { UpdateStaffPositionRequest } from "../types/UpdateStaffPositionRequest.generated";
import { StaffPositionForm } from "../components/StaffPositionForm.generated";
import { StaffPositionTable } from "../components/StaffPositionTable.generated";
import { useStaffPositionControllerListQuery } from "../../operations/useStaffPositionControllerListQuery.react-query.generated";
import { useStaffPositionControllerCreateMutation } from "../../operations/useStaffPositionControllerCreateMutation.react-mutation.generated";
import { useStaffPositionControllerUpdateMutation } from "../../operations/useStaffPositionControllerUpdateMutation.react-mutation.generated";
import { useStaffPositionControllerDeleteMutation } from "../../operations/useStaffPositionControllerDeleteMutation.react-mutation.generated";
import { useStaffPositionControllerSuggestQuery } from "../../operations/useStaffPositionControllerSuggestQuery.react-query.generated";
import type { ListStaffPositionRequest } from "../types/ListStaffPositionRequest.generated";

export function StaffpositionsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Staffpositions</h1>
      </header>
      <TabView>
        <TabPanel header="Staff Positions">
          <StaffPositionSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type StaffPositionEditorState =
  | { readonly mode: "create"; readonly value: CreateStaffPositionRequest }
  | { readonly mode: "edit"; readonly item: StaffPositionDto; readonly value: UpdateStaffPositionRequest }
  | null;

function StaffPositionSection() {
  const [listRequest, setListRequest] = useState<ListStaffPositionRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<StaffPositionDto | null>(null);
  const list = useStaffPositionControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useStaffPositionControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const createMutation = useStaffPositionControllerCreateMutation();
  const updateMutation = useStaffPositionControllerUpdateMutation();
  const deleteMutation = useStaffPositionControllerDeleteMutation();
  const [editor, setEditor] = useState<StaffPositionEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { code: "", description: null, isActive: false, name: "", parentPositionId: null } });
  };
  const openEdit = (item: StaffPositionDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { code: item["code"], description: item["description"], isActive: item["isActive"], name: item["name"], parentPositionId: item["parentPositionId"] } });
  };
  const openDetail = (item: StaffPositionDto) => {
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

  const deleteItem = (item: StaffPositionDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Staff Positions</h2>
        <Button type="button" label="Create StaffPosition" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Staff Positions." />
      ) : null}
      <StaffPositionTable
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
            <h3>Staff Position details</h3>
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
              <dt>Description</dt>
              <dd>{formatDetailValue(detail["description"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Is Active</dt>
              <dd>{formatDetailValue(detail["isActive"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Name</dt>
              <dd>{formatDetailValue(detail["name"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Parent Position Id</dt>
              <dd>{formatDetailValue(detail["parentPositionId"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit StaffPosition" : "Create StaffPosition"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <StaffPositionForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateStaffPositionRequest }
                  : { ...editor, value: value as UpdateStaffPositionRequest },
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

