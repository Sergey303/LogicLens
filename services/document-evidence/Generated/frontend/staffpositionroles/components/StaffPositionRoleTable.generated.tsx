// ------------------------------------------------------------------------------
// GENERATED FILE - source: staffpositionroles/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import { AutoComplete } from "primereact/autocomplete";
import { Button } from "primereact/button";
import { Column } from "primereact/column";
import { DataTable } from "primereact/datatable";
import { MultiSelect } from "primereact/multiselect";
import type { StaffPositionRoleDto } from "../types/StaffPositionRoleDto.generated";

const textFilterMatchModes = [
  { label: "Contains", value: "contains" },
  { label: "Starts with", value: "startsWith" },
  { label: "Equals", value: "equals" },
];

export interface StaffPositionRoleTableOption {
  readonly label: string;
  readonly value: string;
}

export interface StaffPositionRoleTableSort {
  readonly field: string;
  readonly direction: "asc" | "desc";
}

export interface StaffPositionRoleTableFilter {
  readonly field: string;
  readonly operator: "contains" | "startsWith" | "equals" | "in";
  readonly value: string | null;
  readonly values: readonly string[];
}

export interface StaffPositionRoleTableProps {
  readonly items: readonly StaffPositionRoleDto[];
  readonly loading?: boolean;
  readonly rows?: number;
  readonly lazy?: boolean;
  readonly page?: number;
  readonly pageSize?: number;
  readonly totalRecords?: number;
  readonly suggestions?: Readonly<Record<string, readonly string[]>>;
  readonly options?: Readonly<Record<string, readonly StaffPositionRoleTableOption[]>>;
  readonly onSuggest?: (field: string, query: string) => void;
  readonly onPageChange?: (next: { readonly page: number; readonly pageSize: number }) => void;
  readonly onSortChange?: (sort: readonly StaffPositionRoleTableSort[]) => void;
  readonly onFilterChange?: (filters: readonly StaffPositionRoleTableFilter[]) => void;
  readonly onOpen?: (item: StaffPositionRoleDto) => void;
  readonly onEdit?: (item: StaffPositionRoleDto) => void;
  readonly onDelete?: (item: StaffPositionRoleDto) => void;
}

export function StaffPositionRoleTable(props: StaffPositionRoleTableProps) {
  const rows = props.pageSize ?? props.rows ?? 10;
  const first = Math.max(0, ((props.page ?? 1) - 1) * rows);

  return (
    <DataTable
      value={[...props.items]}
      dataKey="id"
      loading={props.loading}
      lazy={Boolean(props.lazy)}
      paginator
      first={first}
      rows={rows}
      totalRecords={props.totalRecords ?? props.items.length}
      rowsPerPageOptions={[10, 25, 50]}
      sortMode="multiple"
      filterDisplay="row"
      emptyMessage="No records found"
      onPage={(event) => props.onPageChange?.({
        page: Math.floor(event.first / event.rows) + 1,
        pageSize: event.rows,
      })}
      onSort={(event) => props.onSortChange?.(readSortEvent(event))}
      onFilter={(event) => props.onFilterChange?.(readFilterEvent(event))}
    >
      <Column
        field="roleId"
        header="Role Id"
        sortable
        filter
        filterMatchMode="contains"
        filterMatchModeOptions={textFilterMatchModes}
        filterElement={(options) => renderTextFilter("roleId", options, props)}
      />
      <Column
        field="staffPositionId"
        header="Staff Position Id"
        sortable
        filter
        filterMatchMode="contains"
        filterMatchModeOptions={textFilterMatchModes}
        filterElement={(options) => renderTextFilter("staffPositionId", options, props)}
      />
      <Column
        header="Actions"
        body={(row: StaffPositionRoleDto) => renderActions(row, props)}
        exportable={false}
      />
    </DataTable>
  );
}

function renderTextFilter(
  field: string,
  options: unknown,
  props: StaffPositionRoleTableProps,
) {
  const filterOptions = asFilterOptions(options);
  return (
    <AutoComplete
      value={readFilterElementText(filterOptions)}
      suggestions={[...(props.suggestions?.[field] ?? [])]}
      completeMethod={(event: { readonly query?: string }) =>
        props.onSuggest?.(field, String(event.query ?? ""))}
      onChange={(event: { readonly value?: unknown }) =>
        filterOptions?.filterApplyCallback?.(readAutoCompleteValue(event.value))}
      dropdown
    />
  );
}

function renderTagsFilter(
  field: string,
  options: unknown,
  props: StaffPositionRoleTableProps,
) {
  const filterOptions = asFilterOptions(options);
  return (
    <MultiSelect
      value={readFilterElementValues(filterOptions)}
      options={[...(props.options?.[field] ?? [])]}
      optionLabel="label"
      optionValue="value"
      display="chip"
      onChange={(event: { readonly value?: unknown }) =>
        filterOptions?.filterApplyCallback?.(readStringArray(event.value))}
    />
  );
}

function readFilterElementText(options: TableFilterOptions | null): string {
  const value = options?.value;
  return typeof value === "string" ? value : "";
}

function readFilterElementValues(options: TableFilterOptions | null): readonly string[] {
  return readStringArray(options?.value);
}

function readAutoCompleteValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }

  if (value === null || value === undefined) {
    return "";
  }

  return String(value);
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => String(item).trim())
    .filter((item) => item.length > 0);
}

interface TableFilterOptions {
  readonly value?: unknown;
  readonly filterApplyCallback?: (value: unknown) => void;
}

function asFilterOptions(value: unknown): TableFilterOptions | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  return value as TableFilterOptions;
}

function readSortEvent(event: unknown): readonly StaffPositionRoleTableSort[] {
  const source = event as {
    readonly multiSortMeta?: readonly { readonly field?: string; readonly order?: number | null }[] | null;
    readonly sortField?: string;
    readonly sortOrder?: number | null;
  };
  const multi = source.multiSortMeta ?? [];
  if (multi.length > 0) {
    return multi
      .filter((item) => typeof item.field === "string" && item.field.length > 0)
      .map((item) => ({ field: item.field ?? "", direction: item.order === -1 ? "desc" : "asc" }));
  }

  if (typeof source.sortField === "string" && source.sortField.length > 0) {
    return [{ field: source.sortField, direction: source.sortOrder === -1 ? "desc" : "asc" }];
  }

  return [];
}

function readFilterEvent(event: unknown): readonly StaffPositionRoleTableFilter[] {
  const source = (event as { readonly filters?: Record<string, unknown> }).filters ?? {};
  const filters: StaffPositionRoleTableFilter[] = [];

  for (const [field, metadata] of Object.entries(source)) {
    const values = readFilterValues(metadata);
    if (values.length > 0) {
      filters.push({ field, operator: "in", value: null, values });
      continue;
    }

    const value = readFilterValue(metadata);
    if (value === null || value.length === 0) {
      continue;
    }

    filters.push({ field, operator: readFilterOperator(metadata), value, values: [] });
  }

  return filters;
}

function readFilterValues(metadata: unknown): readonly string[] {
  const record = asRecord(metadata);
  const candidate = record?.value ?? readFirstConstraintValue(record);
  return readStringArray(candidate);
}

function readFilterValue(metadata: unknown): string | null {
  const record = asRecord(metadata);
  const candidate = record?.value ?? readFirstConstraintValue(record);
  if (Array.isArray(candidate) || candidate === undefined || candidate === null) {
    return null;
  }

  return String(candidate).trim();
}

function readFirstConstraintValue(record: Record<string, unknown> | null): unknown {
  const constraints = record?.constraints;
  if (!Array.isArray(constraints) || constraints.length === 0) {
    return undefined;
  }

  return asRecord(constraints[0])?.value;
}

function readFilterOperator(metadata: unknown): "contains" | "startsWith" | "equals" | "in" {
  const record = asRecord(metadata);
  const matchMode = String(record?.matchMode ?? readFirstConstraintMatchMode(record) ?? "contains");
  if (matchMode === "equals") {
    return "equals";
  }

  if (matchMode === "in") {
    return "in";
  }

  if (matchMode === "startsWith" || matchMode === "starts_with") {
    return "startsWith";
  }

  return "contains";
}

function readFirstConstraintMatchMode(record: Record<string, unknown> | null): unknown {
  const constraints = record?.constraints;
  if (!Array.isArray(constraints) || constraints.length === 0) {
    return undefined;
  }

  return asRecord(constraints[0])?.matchMode;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  return value as Record<string, unknown>;
}

function renderActions(row: StaffPositionRoleDto, props: StaffPositionRoleTableProps) {
  return (
    <div className="appforge-generated-table-actions">
      {props.onOpen ? (
        <Button type="button" label="Open" text onClick={() => props.onOpen?.(row)} />
      ) : null}
      {props.onEdit ? (
        <Button type="button" label="Edit" text onClick={() => props.onEdit?.(row)} />
      ) : null}
      {props.onDelete ? (
        <Button
          type="button"
          label="Delete"
          severity="danger"
          text
          onClick={() => props.onDelete?.(row)}
        />
      ) : null}
    </div>
  );
}

