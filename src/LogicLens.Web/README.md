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

Start `LogicLens.Api` first, then from this directory:

```bash
npm ci
npm run dev
```

By default the browser calls the API on the same origin. For a separate development API:

```bash
VITE_API_BASE_URL=http://localhost:5080 npm run dev
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
