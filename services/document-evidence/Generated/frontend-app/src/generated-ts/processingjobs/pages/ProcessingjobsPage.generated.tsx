// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/endpoints.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { useState } from "react";
import { Button } from "primereact/button";
import { Dialog } from "primereact/dialog";
import { Message } from "primereact/message";
import { TabPanel, TabView } from "primereact/tabview";
import { readFieldErrors } from "../../runtime/validationErrorRuntime";
import type { ProcessingJobDto } from "../types/ProcessingJobDto.generated";
import type { CreateProcessingJobRequest } from "../types/CreateProcessingJobRequest.generated";
import type { UpdateProcessingJobRequest } from "../types/UpdateProcessingJobRequest.generated";
import { ProcessingJobForm } from "../components/ProcessingJobForm.generated";
import { ProcessingJobTable } from "../components/ProcessingJobTable.generated";
import { useProcessingJobControllerListQuery } from "../../operations/useProcessingJobControllerListQuery.react-query.generated";
import { useProcessingJobControllerCreateMutation } from "../../operations/useProcessingJobControllerCreateMutation.react-mutation.generated";
import { useProcessingJobControllerUpdateMutation } from "../../operations/useProcessingJobControllerUpdateMutation.react-mutation.generated";
import { useProcessingJobControllerDeleteMutation } from "../../operations/useProcessingJobControllerDeleteMutation.react-mutation.generated";
import { useProcessingJobControllerSuggestQuery } from "../../operations/useProcessingJobControllerSuggestQuery.react-query.generated";
import { useProcessingJobControllerOptionsQuery } from "../../operations/useProcessingJobControllerOptionsQuery.react-query.generated";
import type { ListProcessingJobRequest } from "../types/ListProcessingJobRequest.generated";

export function ProcessingjobsPage() {
  return (
    <main className="appforge-generated-page">
      <header className="appforge-generated-page-header">
        <h1>Processingjobs</h1>
      </header>
      <TabView>
        <TabPanel header="Processing Jobs">
          <ProcessingJobSection />
        </TabPanel>
      </TabView>
    </main>
  );
}

type ProcessingJobEditorState =
  | { readonly mode: "create"; readonly value: CreateProcessingJobRequest }
  | { readonly mode: "edit"; readonly item: ProcessingJobDto; readonly value: UpdateProcessingJobRequest }
  | null;

function ProcessingJobSection() {
  const [listRequest, setListRequest] = useState<ListProcessingJobRequest>({
    page: 1,
    pageSize: 10,
    filters: [],
    sort: [],
  });
  const [detail, setDetail] = useState<ProcessingJobDto | null>(null);
  const list = useProcessingJobControllerListQuery({ request: listRequest });
  const [suggestRequest, setSuggestRequest] = useState({ field: "__none", query: "" });
  const suggest = useProcessingJobControllerSuggestQuery({
    field: suggestRequest.field,
    request: { query: suggestRequest.query, take: 10 },
  });
  const suggestionItems = suggestRequest.field !== "__none"
    ? { [suggestRequest.field]: (suggest.data ?? []).map((item) => item.value) }
    : {};
  const KindOptions = useProcessingJobControllerOptionsQuery({ field: "kind" });
  const StateOptions = useProcessingJobControllerOptionsQuery({ field: "state" });
  const optionItems = {
    kind: KindOptions.data ?? [],
    state: StateOptions.data ?? [],
  };
  const createMutation = useProcessingJobControllerCreateMutation();
  const updateMutation = useProcessingJobControllerUpdateMutation();
  const deleteMutation = useProcessingJobControllerDeleteMutation();
  const [editor, setEditor] = useState<ProcessingJobEditorState>(null);
  const items = list.data?.items ?? [];
  const totalCount = list.data?.totalCount ?? 0;
  const saving = createMutation.isPending || updateMutation.isPending;

  const resetEditorErrors = () => {
    createMutation.reset();
    updateMutation.reset();
  };

  const openCreate = () => {
    resetEditorErrors();
    setEditor({ mode: "create", value: { attempt: 0, documentRevisionId: "", idempotencyKey: "", kind: "", lastErrorCode: null, leaseUntil: null, state: "" } });
  };
  const openEdit = (item: ProcessingJobDto) => {
    resetEditorErrors();
    setEditor({ mode: "edit", item, value: { attempt: item["attempt"], documentRevisionId: item["documentRevisionId"], idempotencyKey: item["idempotencyKey"], kind: item["kind"], lastErrorCode: item["lastErrorCode"], leaseUntil: item["leaseUntil"], state: item["state"] } });
  };
  const openDetail = (item: ProcessingJobDto) => {
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

  const deleteItem = (item: ProcessingJobDto) => {
    void deleteMutation.execute({ id: item["id"] });
  };

  return (
    <section className="appforge-generated-resource-page-section">
      <div className="appforge-generated-resource-page-toolbar">
        <h2>Processing Jobs</h2>
        <Button type="button" label="Create ProcessingJob" onClick={openCreate} />
      </div>
      {list.error ? (
        <Message severity="error" text="Failed to load Processing Jobs." />
      ) : null}
      <ProcessingJobTable
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
            <h3>Processing Job details</h3>
            <div className="appforge-generated-detail-actions">
              <Button type="button" label="Edit" text onClick={() => openEdit(detail)} />
              <Button type="button" label="Close" text onClick={() => setDetail(null)} />
            </div>
          </div>
          <dl className="appforge-generated-detail-fields">
            <div className="appforge-generated-detail-field">
              <dt>Attempt</dt>
              <dd>{formatDetailValue(detail["attempt"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Document Revision Id</dt>
              <dd>{formatDetailValue(detail["documentRevisionId"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Idempotency Key</dt>
              <dd>{formatDetailValue(detail["idempotencyKey"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Kind</dt>
              <dd>{formatDetailValue(detail["kind"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Last Error Code</dt>
              <dd>{formatDetailValue(detail["lastErrorCode"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>Lease Until</dt>
              <dd>{formatDetailValue(detail["leaseUntil"])}</dd>
            </div>
            <div className="appforge-generated-detail-field">
              <dt>State</dt>
              <dd>{formatDetailValue(detail["state"])}</dd>
            </div>
          </dl>
        </section>
      ) : null}
      <Dialog
        visible={editor !== null}
        header={editor?.mode === "edit" ? "Edit ProcessingJob" : "Create ProcessingJob"}
        modal
        onHide={closeEditor}
      >
        {editor ? (
          <ProcessingJobForm
            value={editor.value}
            onChange={(value) => {
              setEditor(
                editor.mode === "create"
                  ? { mode: "create", value: value as CreateProcessingJobRequest }
                  : { ...editor, value: value as UpdateProcessingJobRequest },
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

