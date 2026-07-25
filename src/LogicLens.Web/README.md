# LogicLens.Web

Universal React renderer for the validated UI Document v0 contract.

The web application does not know domain types such as people, organizations, or documents. It renders only the closed component vocabulary from `contracts/ui-document-v0.schema.json`:

- Page;
- nested Section;
- Property;
- TextBlock;
- RawProlog;
- Diagnostic;
- TextValue;
- ResourceLinkValue.

## Local run

From the repository root, start the API on the port used by the Vite proxy:

```bash
ASPNETCORE_URLS=http://localhost:5080 dotnet run \
  --project src/LogicLens.Api/LogicLens.Api.csproj
```

Then, from `src/LogicLens.Web`:

```bash
npm ci
npm run dev
```

The browser calls `/api` on the Vite origin. Vite proxies those requests to `http://localhost:5080`, so the API does not need a development CORS policy. To use another local API address:

```bash
LOGICLENS_API_URL=http://localhost:5090 npm run dev
```

Open an entity with either form:

```text
/entities/<URL-encoded entity id>
?entity=<entity id>
```

The default fixture entity is `urn:logiclens:person:alex`.

## Verification

```bash
npm test
npm run build
```

The tests use server rendering to verify nested occurrences, direction distinction, technical-section collapse, safe RawProlog text, edit affordances, derived read-only values, resource links, unknown component fallback, and isolation of a damaged component.
