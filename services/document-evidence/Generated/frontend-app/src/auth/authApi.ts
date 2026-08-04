import { getHttpClient } from "../generated-ts/runtime/httpClient";

export interface AuthUserDto {
  id: string;
  email: string;
  userName: string;
  mustChangePassword: boolean;
  emailConfirmed: boolean;
  roles: string[];
  permissions: string[];
}

export interface AuthSession {
  accessToken: string;
  expiresAtUtc: string;
  user: AuthUserDto;
}

interface AuthResponse extends AuthSession {
  refreshToken: string;
}

let sessionMemory: AuthSession | null = null;

export function getAuthSession(): AuthSession | null {
  return sessionMemory;
}

export function getAuthAccessToken(): string | null {
  return sessionMemory?.accessToken ?? null;
}

export function setAuthSession(response: AuthResponse): AuthSession {
  sessionMemory = {
    accessToken: response.accessToken,
    expiresAtUtc: response.expiresAtUtc,
    user: response.user,
  };
  notifyAuthChanged();
  return sessionMemory;
}

export function clearAuthSession(): void {
  sessionMemory = null;
  notifyAuthChanged();
}

export async function loginAuth(login: string, password: string): Promise<AuthSession> {
  try {
    const response = await postJson<AuthResponse>(
      "/api/auth/login",
      { login, password },
    );

    return setAuthSession(response);
  }
  catch {
    throw new Error("Invalid login or password.");
  }
}

export async function logoutAuth(): Promise<void> {
  try {
    if (getAuthAccessToken()) {
      await postNoContent("/api/auth/logout", {});
    }
  }
  catch {
    // Local logout remains authoritative when the server session is unavailable.
  }
  finally {
    clearAuthSession();
  }
}

export async function changePasswordAuth(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await postNoContent(
    "/api/auth/change-password",
    { currentPassword, newPassword },
  );
}

async function postJson<TResponse>(
  path: string,
  body: unknown,
): Promise<TResponse> {
  const result = await getHttpClient().call<TResponse, "json">({
    method: "POST",
    url: path,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    responseMode: "json",
  });

  return result.data;
}

async function postNoContent(
  path: string,
  body: unknown,
): Promise<void> {
  await getHttpClient().call<never, "none">({
    method: "POST",
    url: path,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    responseMode: "none",
  });
}

function notifyAuthChanged(): void {
  window.dispatchEvent(new Event("appforge-auth-changed"));
}
