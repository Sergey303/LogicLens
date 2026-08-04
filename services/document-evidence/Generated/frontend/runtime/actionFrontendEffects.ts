import { assignSafeLocation } from "../../../security/urlSafety";
import type { BinaryTransportPayload, FrontendActionMetadata } from "./transportTypes";

export function performFrontendAction(frontendAction: FrontendActionMetadata | null, payload: unknown): void {
  if (!frontendAction) {
    return;
  }

  if (frontendAction.actionKind === "windowLocationAssign" && typeof payload === "string") {
    assignSafeLocation(payload);
    return;
  }

  if (frontendAction.actionKind === "download") {
    if (!isBinaryTransportPayload(payload)) {
      throw new Error("[actionRuntime] Download action requires binary transport payload.");
    }
    performBinaryDownload(payload);
    return;
  }

  if (frontendAction.actionKind === "upload") {
    return;
  }

  throw new Error(
    `[actionRuntime] Unsupported frontend action kind '${frontendAction.actionKind}' for action endpoint. ` +
    `The current runtime supports 'windowLocationAssign', 'download', and 'upload'. ` +
    `Add support for '${frontendAction.actionKind}' in performFrontendAction() when the canonical frontendAction metadata expands.`
  );
}

function isBinaryTransportPayload(payload: unknown): payload is BinaryTransportPayload {
  if (!payload || typeof payload !== "object") {
    return false;
  }

  return "blob" in payload;
}

function performBinaryDownload(payload: BinaryTransportPayload): void {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return;
  }

  const downloadUrl = URL.createObjectURL(payload.blob);
  const anchor = document.createElement("a");
  anchor.href = downloadUrl;
  anchor.download = payload.fileName ?? "download";
  anchor.style.display = "none";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(downloadUrl);
}
