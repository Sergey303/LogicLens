import {
  Suspense,
  useSyncExternalStore,
} from "react";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { configureHttpClient } from "./generated-ts/runtime/httpClient";
import { AccountSettingsPage } from "./auth/AccountSettingsPage";
import {
  getForbidden,
  clearForbidden,
  subscribeForbidden,
} from "./auth/authBoundary";
import {
  AuthProvider,
  useAuth,
} from "./auth/AuthProvider";
import { ForbiddenPage } from "./auth/ForbiddenPage";
import { LoginPage } from "./auth/LoginPage";
import { createProductionHttpClient } from "./auth/productionHttpClient";
import { ErrorBoundary } from "./ErrorBoundary";
import { generatedPages } from "./generatedPages";
import { getApiBaseUrl } from "./runtimeConfig";

const queryClient = new QueryClient();

configureHttpClient(
  createProductionHttpClient(getApiBaseUrl()),
);

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <AuthProvider>
          <Suspense
            fallback={
              <main className="appforge-message-page">
                Loading generated admin...
              </main>
            }
          >
            <AuthenticatedApp />
          </Suspense>
        </AuthProvider>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

function AuthenticatedApp() {
  const auth = useAuth();

  if (!auth.session) {
    return <LoginPage />;
  }

  if (auth.session.user.mustChangePassword) {
    return <ForcedPasswordChangeShell />;
  }

  return <AppShell />;
}

function ForcedPasswordChangeShell() {
  const auth = useAuth();

  return (
    <div className="appforge-shell">
      <aside className="appforge-sidebar">
        <h1>AppForge Admin</h1>

        <p className="appforge-user">
          {auth.session?.user.email}
        </p>

        <p>
          Password change is required before using the application.
        </p>

        <button
          className="appforge-logout"
          type="button"
          onClick={() => void auth.logout()}
        >
          Sign out
        </button>
      </aside>

      <section className="appforge-content">
        <AccountSettingsPage forceChangePassword />
      </section>
    </div>
  );
}

function AppShell() {
  const auth = useAuth();
  const activeRoute = useHashRoute();
  const forbidden = useForbidden();

  const showingAccount = activeRoute === "/account";

  const activePage =
    generatedPages.find(
      (page) => page.route === activeRoute,
    ) ?? generatedPages[0];

  return (
    <div className="appforge-shell">
      <aside className="appforge-sidebar">
        <h1>AppForge Admin</h1>

        <p className="appforge-user">
          {auth.session?.user.email}
        </p>

        <nav aria-label="Generated pages">
          {generatedPages.map((page) => (
            <a
              key={page.route}
              className={
                !showingAccount &&
                page.route === activePage?.route
                  ? "is-active"
                  : ""
              }
              href={"#" + page.route}
              onClick={clearForbidden}
            >
              {page.title}
            </a>
          ))}

          <a
            className={showingAccount ? "is-active" : ""}
            href="#/account"
            onClick={clearForbidden}
          >
            Account
          </a>
        </nav>

        <button
          className="appforge-logout"
          type="button"
          onClick={() => void auth.logout()}
        >
          Sign out
        </button>
      </aside>

      <section className="appforge-content">
        {forbidden ? (
          <ForbiddenPage />
        ) : showingAccount ? (
          <AccountSettingsPage />
        ) : (
          activePage?.element
        )}
      </section>
    </div>
  );
}

function useForbidden(): boolean {
  return useSyncExternalStore(
    subscribeForbidden,
    getForbidden,
    getForbidden,
  );
}

function useHashRoute(): string {
  return useSyncExternalStore(
    subscribeHash,
    getHashRoute,
    getHashRoute,
  );
}

function subscribeHash(
  onStoreChange: () => void,
): () => void {
  window.addEventListener(
    "hashchange",
    onStoreChange,
  );

  return () => {
    window.removeEventListener(
      "hashchange",
      onStoreChange,
    );
  };
}

function getHashRoute(): string {
  const hash = window.location.hash;

  const route = hash.startsWith("#")
    ? hash.slice(1)
    : hash;

  if (!route) {
    return generatedPages[0]?.route ?? "/";
  }

  return route.startsWith("/")
    ? route
    : "/" + route;
}
