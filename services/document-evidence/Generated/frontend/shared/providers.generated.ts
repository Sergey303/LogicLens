// ------------------------------------------------------------------------------
// GENERATED FILE - source: shared/providers.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import providersCatalogJson from "./providers.generated.json";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function mergeInto(target: Record<string, unknown>, source: Record<string, unknown>): void {
  for (const [key, value] of Object.entries(source)) {
    const current = target[key];
    if (Array.isArray(current) && Array.isArray(value)) {
      target[key] = [...current, ...value];
    } else if (isRecord(current) && isRecord(value)) {
      mergeInto(current, value);
    } else {
      target[key] = value;
    }
  }
}

function mergeCatalogFragments(...fragments: readonly Record<string, unknown>[]): Record<string, unknown> {
  const merged: Record<string, unknown> = {};
  for (const fragment of fragments) mergeInto(merged, fragment);
  return merged;
}

const providersCatalogMergedJson = mergeCatalogFragments(providersCatalogJson);
export const providersCatalog: Readonly<typeof providersCatalogMergedJson> = providersCatalogMergedJson;
