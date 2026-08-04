import type {
  HttpCallResult,
  HttpClient,
  HttpRequestDescriptor,
  HttpResponseMode,
} from "../generated-ts/runtime/httpClient";
import {
  createBrowserHttpClient,
} from "../generated-ts/runtime/browserHttpClient";
import {
  clearAuthSession,
  getAuthAccessToken,
} from "./authApi";
import { markForbidden } from "./authBoundary";

export function createProductionHttpClient(
  apiBaseUrl: string,
): HttpClient {
  return {
    async call<TJson, TResponseMode extends HttpResponseMode>(
      request: HttpRequestDescriptor<TResponseMode>,
    ): Promise<HttpCallResult<TJson, TResponseMode>> {
      const accessToken = getAuthAccessToken();

      const client = createBrowserHttpClient({
        apiBaseUrl,
        credentials: "include",
        headers: accessToken
          ? {
              Authorization: "Bearer " + accessToken,
            }
          : undefined,
        onUnauthorized: () => {
          clearAuthSession();
        },
        onForbidden: () => {
          markForbidden();
        },
      });

      return await client.call<TJson, TResponseMode>(
        request,
      );
    },
  };
}
