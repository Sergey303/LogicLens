import type { ReactNode } from "react";
import type {
  DiagnosticComponent,
  PropertyComponent,
  SectionComponent,
  UiDocument,
  UiValue,
  ValueSource,
} from "../model/uiDocument";

export interface UiDocumentRendererProps {
  document: UiDocument;
}

export function UiDocumentRenderer({ document }: UiDocumentRendererProps) {
  return (
    <main className="ui-document" data-schema-version={document.schemaVersion}>
      <header className="page-header">
        <p className="document-meta">
          Эпоха {document.epoch}, ревизия {document.revision}
        </p>
        <h1>{document.page.title}</h1>
      </header>

      {document.diagnostics.length > 0 && (
        <section className="page-diagnostics" aria-label="Диагностика страницы">
          {document.diagnostics.map((diagnostic) =>
            renderDiagnostic(diagnostic, "page"),
          )}
        </section>
      )}

      <div className="page-sections">
        {document.page.sections.map((section) =>
          renderSection(section, 0),
        )}
      </div>
    </main>
  );
}

function renderSection(section: SectionComponent, nestingDepth: number): ReactNode {
  const body = (
    <div className="section-body">
      {section.occurrence && (
        <OccurrenceSummary occurrence={section.occurrence} />
      )}
      <div className="section-components">
        {section.components.map((component, index) =>
          renderComponentSafely(component, nestingDepth + 1, index),
        )}
      </div>
    </div>
  );

  const common = {
    key: section.id,
    className: `ui-section ui-section--${section.presentation}`,
    "data-component-id": section.id,
    "data-presentation": section.presentation,
    "data-nesting-depth": nestingDepth,
    ...(section.occurrence
      ? { "data-occurrence-id": section.occurrence.occurrenceId }
      : {}),
  };

  if (section.presentation === "default") {
    return (
      <section {...common}>
        <h2>{section.title}</h2>
        {body}
      </section>
    );
  }

  return (
    <details {...common}>
      <summary>{section.title}</summary>
      {body}
    </details>
  );
}

function renderComponentSafely(
  component: unknown,
  nestingDepth: number,
  index: number,
): ReactNode {
  const fallbackId = `invalid:${nestingDepth}:${index}`;

  try {
    if (!isRecord(component) || typeof component.kind !== "string") {
      return renderLocalFailure(fallbackId, "Компонент не имеет допустимого kind.");
    }

    switch (component.kind) {
      case "section":
        return renderSection(component as unknown as SectionComponent, nestingDepth);
      case "property":
        return renderProperty(component as unknown as PropertyComponent);
      case "textBlock":
        return (
          <p
            key={requiredString(component, "id")}
            className="text-block"
            data-component-id={requiredString(component, "id")}
          >
            {requiredString(component, "text")}
          </p>
        );
      case "rawProlog":
        return (
          <section
            key={requiredString(component, "id")}
            className="raw-prolog"
            data-component-id={requiredString(component, "id")}
          >
            <h3>{requiredString(component, "title")}</h3>
            <p className="artifact-kind">
              {requiredString(component, "artifactKind")}
            </p>
            <pre>
              <code>{requiredString(component, "code")}</code>
            </pre>
          </section>
        );
      case "diagnostic":
        return renderDiagnostic(
          component as unknown as DiagnosticComponent,
          "component",
        );
      default:
        return renderLocalFailure(
          optionalString(component, "id") ?? fallbackId,
          `Компонент kind '${component.kind}' не поддерживается UI Document v0.`,
        );
    }
  } catch {
    const componentId = isRecord(component)
      ? optionalString(component, "id") ?? fallbackId
      : fallbackId;
    return renderLocalFailure(
      componentId,
      "Компонент не удалось отобразить. Остальная страница сохранена.",
    );
  }
}

function renderProperty(property: PropertyComponent): ReactNode {
  const values = property.values.map((value, index) =>
    renderValue(value, `${property.id}:value:${index}`),
  );

  return (
    <section
      key={property.id}
      className={`property property--${property.direction}`}
      data-component-id={property.id}
      data-direction={property.direction}
    >
      <header className="property-header">
        <h3>{property.label}</h3>
        <span className="direction-badge">
          {directionLabel(property.direction)}
        </span>
      </header>
      <p className="predicate-id">{property.predicate}</p>
      <ul className="property-values">{values}</ul>
    </section>
  );
}

function renderValue(value: UiValue, key: string): ReactNode {
  if (value.kind === "text") {
    return (
      <li key={key} className="property-value property-value--text">
        <span className="value-primary">{value.text}</span>
        <ValueMetadata value={value} />
        <EditAffordance editable={value.editable} source={value.source} />
        <SourceDetails source={value.source} />
      </li>
    );
  }

  if (value.kind === "resourceLink") {
    return (
      <li key={key} className="property-value property-value--resource">
        <a className="resource-link" href={entityHref(value.targetId)}>
          {value.label || value.targetId}
        </a>
        <code className="resource-id">{value.targetId}</code>
        <EditAffordance editable={value.editable} source={value.source} />
        <SourceDetails source={value.source} />
      </li>
    );
  }

  throw new Error("Unsupported value kind.");
}

function ValueMetadata({ value }: { value: Extract<UiValue, { kind: "text" }> }) {
  const metadata = [
    value.language ? `lang=${value.language}` : null,
    value.datatype ? `datatype=${value.datatype}` : null,
    value.literalKind,
  ].filter((item): item is string => item !== null);

  return <small className="value-metadata">{metadata.join(" · ")}</small>;
}

function EditAffordance({
  editable,
  source,
}: {
  editable: boolean;
  source: ValueSource;
}) {
  const canEdit = editable === true && source.kind === "base";
  if (canEdit) {
    return (
      <span className="edit-affordance" aria-label="Значение доступно для редактирования">
        Изменяемое
      </span>
    );
  }

  if (source.kind === "derived") {
    return <span className="derived-badge">Вычислено, только чтение</span>;
  }

  return null;
}

function SourceDetails({ source }: { source: ValueSource }) {
  if (source.kind === "base") {
    return (
      <details className="source-details">
        <summary>Источник</summary>
        <dl>
          <dt>FactId</dt>
          <dd>{source.fact.factId}</dd>
          <dt>Origins</dt>
          <dd>{source.origins.join(", ")}</dd>
        </dl>
      </details>
    );
  }

  return (
    <details className="source-details">
      <summary>Доказательство</summary>
      <dl>
        <dt>Правило</dt>
        <dd>{source.ruleId}</dd>
        <dt>Факты</dt>
        <dd>{source.evidenceFactIds.join(", ")}</dd>
      </dl>
    </details>
  );
}

function OccurrenceSummary({
  occurrence,
}: {
  occurrence: SectionComponent["occurrence"] & {};
}) {
  return (
    <dl className="occurrence-summary">
      <dt>Узел</dt>
      <dd>{occurrence.nodeId}</dd>
      <dt>Глубина</dt>
      <dd>{occurrence.depth}</dd>
      <dt>Состояние</dt>
      <dd>{occurrenceStateLabel(occurrence.state)}</dd>
    </dl>
  );
}

function renderDiagnostic(
  diagnostic: DiagnosticComponent,
  scope: "page" | "component",
): ReactNode {
  return (
    <aside
      key={`${scope}:${diagnostic.id}`}
      className={`diagnostic diagnostic--${diagnostic.severity}`}
      data-component-id={diagnostic.id}
      data-diagnostic-scope={scope}
      role={diagnostic.severity === "error" ? "alert" : "status"}
    >
      <strong>{severityLabel(diagnostic.severity)}</strong>
      <span>{diagnostic.message}</span>
    </aside>
  );
}

function renderLocalFailure(id: string, message: string): ReactNode {
  return renderDiagnostic(
    {
      kind: "diagnostic",
      id: `renderer:${id}`,
      severity: "error",
      message,
    },
    "component",
  );
}

function entityHref(entityId: string): string {
  return `/entities/${encodeURIComponent(entityId)}`;
}

function directionLabel(direction: PropertyComponent["direction"]): string {
  switch (direction) {
    case "outgoing":
      return "Исходящая связь";
    case "incoming":
      return "Входящая связь";
    case "derived":
      return "Вычислено";
  }
}

function severityLabel(severity: DiagnosticComponent["severity"]): string {
  switch (severity) {
    case "info":
      return "Информация";
    case "warning":
      return "Предупреждение";
    case "error":
      return "Ошибка";
  }
}

function occurrenceStateLabel(
  state: NonNullable<SectionComponent["occurrence"]>["state"],
): string {
  switch (state) {
    case "expanded":
      return "раскрыт";
    case "boundary":
      return "граница";
    case "cycle_reference":
      return "ссылка на цикл";
    case "limited":
      return "ограничен";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiredString(value: Record<string, unknown>, field: string): string {
  const result = optionalString(value, field);
  if (result === null) {
    throw new Error(`Field '${field}' is missing.`);
  }
  return result;
}

function optionalString(
  value: Record<string, unknown>,
  field: string,
): string | null {
  return typeof value[field] === "string" ? value[field] : null;
}
