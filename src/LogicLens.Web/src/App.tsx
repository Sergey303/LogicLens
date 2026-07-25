import { useEffect, useMemo, useState } from "react";
import { EntityApiError, loadEntityView } from "./api/entityApi";
import type { UiDocument } from "./model/uiDocument";
import { UiDocumentRenderer } from "./rendering/UiDocumentRenderer";

const defaultEntityId = "urn:logiclens:person:alex";

export function App() {
  const initialEntityId = useMemo(readEntityIdFromLocation, []);
  const [entityId, setEntityId] = useState(initialEntityId);
  const [language, setLanguage] = useState("ru");
  const [document, setDocument] = useState<UiDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    loadEntityView(entityId, language, controller.signal)
      .then((result) => {
        setDocument(result);
        setLoading(false);
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        setDocument(null);
        setError(formatError(reason));
        setLoading(false);
      });

    return () => controller.abort();
  }, [entityId, language]);

  function openEntity(nextEntityId: string) {
    const normalized = nextEntityId.trim();
    if (normalized.length === 0) {
      return;
    }
    window.history.pushState({}, "", entityHref(normalized));
    setEntityId(normalized);
  }

  return (
    <div className="app-shell">
      <nav className="app-toolbar" aria-label="Навигация LogicLens">
        <a className="brand" href={entityHref(defaultEntityId)}>
          LogicLens
        </a>
        <EntitySelector entityId={entityId} onOpen={openEntity} />
        <label className="language-selector">
          Язык
          <select
            value={language}
            onChange={(event) => setLanguage(event.currentTarget.value)}
          >
            <option value="ru">Русский</option>
            <option value="en">English</option>
          </select>
        </label>
      </nav>

      {loading && <p className="status-panel">Загрузка представления…</p>}
      {error && (
        <aside className="status-panel status-panel--error" role="alert">
          <strong>Не удалось загрузить сущность.</strong>
          <span>{error}</span>
        </aside>
      )}
      {document && <UiDocumentRenderer document={document} />}
    </div>
  );
}

function EntitySelector({
  entityId,
  onOpen,
}: {
  entityId: string;
  onOpen: (entityId: string) => void;
}) {
  const [draft, setDraft] = useState(entityId);

  useEffect(() => setDraft(entityId), [entityId]);

  return (
    <form
      className="entity-selector"
      onSubmit={(event) => {
        event.preventDefault();
        onOpen(draft);
      }}
    >
      <label htmlFor="entity-id">Идентификатор сущности</label>
      <input
        id="entity-id"
        value={draft}
        onChange={(event) => setDraft(event.currentTarget.value)}
        autoComplete="off"
      />
      <button type="submit">Открыть</button>
    </form>
  );
}

function readEntityIdFromLocation(): string {
  const prefix = "/entities/";
  if (window.location.pathname.startsWith(prefix)) {
    const encoded = window.location.pathname.slice(prefix.length);
    if (encoded.length > 0) {
      try {
        return decodeURIComponent(encoded);
      } catch {
        return encoded;
      }
    }
  }

  const queryEntity = new URLSearchParams(window.location.search).get("entity");
  return queryEntity?.trim() || defaultEntityId;
}

function entityHref(entityId: string): string {
  return `/entities/${encodeURIComponent(entityId)}`;
}

function formatError(reason: unknown): string {
  if (reason instanceof EntityApiError) {
    return reason.code ? `${reason.message} (${reason.code})` : reason.message;
  }
  if (reason instanceof Error) {
    return reason.message;
  }
  return "Неизвестная ошибка.";
}
