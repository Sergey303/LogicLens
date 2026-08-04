export function extractFileNameFromContentDisposition(contentDisposition: string | null): string | null {
  if (!contentDisposition) {
    return null;
  }

  const utf8Match = /filename\*=UTF-8''([^;]+)/i.exec(contentDisposition);
  if (utf8Match && utf8Match[1]) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch {
      return utf8Match[1];
    }
  }

  const quotedMatch = /filename=\"([^\"]+)\"/i.exec(contentDisposition);
  if (quotedMatch && quotedMatch[1]) {
    return quotedMatch[1];
  }

  const bareMatch = /filename=([^;]+)/i.exec(contentDisposition);
  if (bareMatch && bareMatch[1]) {
    return bareMatch[1].trim();
  }

  return null;
}
