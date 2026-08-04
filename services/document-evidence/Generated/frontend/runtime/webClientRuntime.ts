import { configureHttpClient } from "./httpClient";
import { createFetchHttpClient, type FetchHttpClientOptions } from "./fetchHttpClient";

export interface BackendContractWebClientOptions extends FetchHttpClientOptions {}

let initialized = false;

/**
 * Initializes the generated backend contract runtime with a browser fetch client.
 *
 * This function is safe to call more than once. The first call wins so app
 * bootstrap can call it deterministically in dev/test setups.
 */
export function initializeBackendContractWebClient(options: BackendContractWebClientOptions): void {
  if (initialized) {
    return;
  }

  configureHttpClient(createFetchHttpClient(options));
  initialized = true;
}
