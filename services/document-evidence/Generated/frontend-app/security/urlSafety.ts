export function assignSafeLocation(url: string): void {
  const parsed = new URL(url, window.location.href);
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`[appforge] Unsafe navigation protocol: ${parsed.protocol}`);
  }

  window.location.assign(parsed.toString());
}
