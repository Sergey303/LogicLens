// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ListProcessingJobFilter } from "./ListProcessingJobFilter.generated";
import type { ListProcessingJobSort } from "./ListProcessingJobSort.generated";

export interface ListProcessingJobRequest {
  "filters": ListProcessingJobFilter[];
  "page": number;
  "pageSize": number;
  "sort": ListProcessingJobSort[];
}
export const ListProcessingJobRequestTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListProcessingJobRequest" as const;

