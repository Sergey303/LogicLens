# Zero-epoch local run

This runbook starts the complete LogicLens A1 vertical slice with one command:

- builds the .NET solution;
- installs the committed React dependency graph with `npm ci`;
- builds the production React bundle;
- creates a fresh portable active epoch-000 package;
- starts `LogicLens.Api`;
- starts Vite with the same-origin `/api` proxy;
- verifies the API, proxy and entity routes;
- opens the generic entity page;
- stops both process trees on Ctrl+C.

SWI-Prolog remains behind the closed JSON CLI. The browser never executes Prolog and does not call SWI directly.

## Requirements

The following executables must be available on `PATH`:

```text
Python 3.12+
dotnet 8
Node.js 24 + npm
SWI-Prolog 9.0.4
git
```

## Windows PowerShell

From the repository root:

```powershell
python .\tools\run_zero_epoch.py
```

The default addresses are:

```text
React/Vite: http://127.0.0.1:5173
ASP.NET API: http://127.0.0.1:5080
```

Prepared files and logs are placed in:

```text
.logiclens/zero-epoch/
```

This directory is disposable and ignored by Git.

## Verification-only mode

CI and local diagnostics use the same command path:

```powershell
python .\tools\run_zero_epoch.py --verify-only --no-browser
```

It prepares the complete runtime, starts both services, verifies the vertical slice and stops them.

The verification covers:

- direct ASP.NET health;
- health through the Vite `/api` proxy;
- equality of direct and proxied JSON;
- React root and served entry module;
- browser routes for a person, organization and document;
- valid UI Document v0 context for all three entity kinds;
- byte-identical repeated entity-view responses;
- HTTP 404 for an unknown `/api` route rather than React fallback HTML;
- clean shutdown of API and web process trees.

## Optional parameters

```powershell
python .\tools\run_zero_epoch.py `
  --api-url http://127.0.0.1:5180 `
  --web-url http://127.0.0.1:5273 `
  --no-browser
```

Both origins must use explicit loopback ports. The runner refuses non-loopback addresses so the local development command cannot accidentally expose the research runtime on the network.

Use another SWI executable name or absolute path with:

```powershell
python .\tools\run_zero_epoch.py --swipl swipl
```

## Failure diagnostics

The runner fails immediately when preparation, API readiness, proxying or entity verification fails. Service logs remain at:

```text
.logiclens/zero-epoch/logs/api.log
.logiclens/zero-epoch/logs/web.log
```

A new run replaces the disposable `.logiclens/zero-epoch` directory, so stale epoch data cannot silently affect the result.
