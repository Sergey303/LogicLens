interface AppForgeRuntimeConfig {
  apiBaseUrl?: string;
}

declare global {
  interface Window {
    __APPFORGE_CONFIG__?: AppForgeRuntimeConfig;
  }
}

export function getApiBaseUrl(): string {
  const value = window.__APPFORGE_CONFIG__?.apiBaseUrl ?? import.meta.env.VITE_APPFORGE_API_BASE_URL ?? "";
  return trimTrailingSlashes(value);
}

function trimTrailingSlashes(value: string): string {
  let result = value.trim();
  while (result.endsWith("/")) result = result.slice(0, -1);
  return result;
}
