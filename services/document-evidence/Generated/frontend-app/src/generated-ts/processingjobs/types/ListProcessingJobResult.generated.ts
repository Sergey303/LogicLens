// ------------------------------------------------------------------------------
// GENERATED FILE - source: processingjobs/types.json
// DO NOT EDIT MANUALLY.
// ------------------------------------------------------------------------------

import type { ProcessingJobDto } from "./ProcessingJobDto.generated";

export interface ListProcessingJobResult {
  "items": ProcessingJobDto[];
  "page": number;
  "pageSize": number;
  "totalCount": number;
}
export const ListProcessingJobResultTypeKey = "LogicLens.DocumentEvidence.Generated.Api.Contracts.ListProcessingJobResult" as const;

