import type { UiDocument } from "../model/uiDocument";

export class EntityApiError extends Error {
  public constructor(
    message: string,
    public readonly status: number,
    public readonly code: string | null,
  ) {
    super(message);
    this.name = "EntityApiError";
  }
}

export async function loadEntityView(
  entityId: string,
  language: string,
  signal: AbortSignal,
): Promise<UiDocument> {
  const apiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
    /\/$/,
    "",
  ) ?? "";
  const query = new URLSearchParams({
    language,
    includeProlog: "true",
  });
  const response = await fetch(
    `${apiBase}/api/entities/${encodeURIComponent(entityId)}/view?${query}`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      signal,
    },
  );

  if (!response.ok) {
    const problem = await readProblem(response);
    throw new EntityApiError(
      problem?.title ?? `API returned HTTP ${response.status}.`,
      response.status,
      problem?.code ?? null,
    );
  }

  return (await response.json()) as UiDocument;
}

async function readProblem(
  response: Response,
): Promise<{ title?: string; code?: string } | null> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("json")) {
    return null;
  }

  try {
    return (await response.json()) as { title?: string; code?: string };
  } catch {
    return null;
  }
}
