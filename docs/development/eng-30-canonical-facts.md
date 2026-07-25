# ENG-30 canonical facts and FactId v1

## Scope

This implementation contains only the deterministic foundation required before SWI-Prolog integration:

- typed IRI and literal objects;
- canonical facts;
- FactId v1 byte encoding and SHA-256 identity;
- origin metadata;
- graph deduplication with collision checks;
- a strict importer for the observed FOG RDF/XML subset;
- a zero-dependency verification executable.

It does not contain runtime editing, journal persistence, Prolog rules, API, React, Builder, or Search.

## Requirements

- .NET 8 SDK

No NuGet test packages are required.

## Build

```powershell
dotnet build .\LogicLens.sln
```

## Verify

Run from any directory inside the repository:

```powershell
dotnet run --project .\tests\LogicLens.Core.Verification\LogicLens.Core.Verification.csproj
```

The verifier checks:

1. all FactId v1 golden canonical byte streams;
2. all expected SHA-256 FactIds;
3. both zero-epoch FOG files;
4. exactly 29 unique normalized facts;
5. complete origin lists;
6. duplicate occurrence collapse;
7. language-tag lower-casing;
8. preservation of literal lexical whitespace;
9. rejection of nested XML outside the supported FOG subset.

Success output:

```text
LogicLens.Core verification passed.
```

## Supported FOG subset

The importer accepts:

```xml
<rdf:RDF dbid="...">
  <type rdf:about="subject">
    <literal-property>text</literal-property>
    <literal-property xml:lang="ru">text</literal-property>
    <literal-property rdf:datatype="datatype-iri">text</literal-property>
    <link-property rdf:resource="object-iri" />
  </type>
</rdf:RDF>
```

For each entity element it creates an implicit `rdf:type` fact from the expanded element name.

The importer deliberately rejects:

- a missing `dbid`;
- a missing `rdf:about`;
- unqualified entity/property names;
- nested property elements;
- a literal with both `xml:lang` and `rdf:datatype`;
- `rdf:resource` combined with literal content.

Unsupported input is an error, not silently ignored data.

## Identity boundary

Fact identity is determined only by:

```text
Subject + Predicate + tagged Object
```

Origins do not affect FactId. The same triple from several files has one FactId and several origins.

The importer receives origin resolution as a callback. This prevents ENG-30 from prematurely fixing a production origin-ID convention while still allowing the fixture to use its explicit origin manifest.

## Verification limitation

The ChatGPT execution environment used to prepare this branch did not contain a .NET SDK, so the C# project could not be compiled there. The algorithm and fixture expectations were independently checked, and the repository verifier is the authoritative build-time gate. The PR must not be merged until `dotnet build` and the verifier succeed in a .NET 8 environment.
