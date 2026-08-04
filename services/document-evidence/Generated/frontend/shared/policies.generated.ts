// ------------------------------------------------------------------------------
// GENERATED FILE - source: shared/policies.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import policiesCatalogJson0 from "./policies.generated_0.json";
import policiesCatalogJson1 from "./policies.generated_1.json";
import policiesCatalogJson2 from "./policies.generated_2.json";
import policiesCatalogJson3 from "./policies.generated_3.json";
import policiesCatalogJson4 from "./policies.generated_4.json";
import policiesCatalogJson5 from "./policies.generated_5.json";
import policiesCatalogJson6 from "./policies.generated_6.json";
import policiesCatalogJson7 from "./policies.generated_7.json";

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

const policiesCatalogMergedJson = mergeCatalogFragments(policiesCatalogJson0, policiesCatalogJson1, policiesCatalogJson2, policiesCatalogJson3, policiesCatalogJson4, policiesCatalogJson5, policiesCatalogJson6, policiesCatalogJson7);
export const policiesCatalog: Readonly<typeof policiesCatalogMergedJson> = policiesCatalogMergedJson;
