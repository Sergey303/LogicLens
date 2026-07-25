import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type {
  BaseSource,
  SectionComponent,
  UiDocument,
} from "../model/uiDocument";
import { UiDocumentRenderer } from "./UiDocumentRenderer";

const person = "urn:logiclens:person:alex";
const organization = "urn:logiclens:organization:isi";
const unknownPredicate = "urn:logiclens:predicate:unclassified-42";

function source(
  factId: string,
  subject: string,
  predicate: string,
  object: BaseSource["fact"]["object"],
): BaseSource {
  return {
    kind: "base",
    fact: { factId, subject, predicate, object },
    origins: [`origin:${factId}`],
  };
}

function fixture(): UiDocument {
  const firstOccurrence: SectionComponent = {
    kind: "section",
    id: "section:path:study",
    title: "Связь через обучение",
    presentation: "collapsed",
    occurrence: {
      occurrenceId: "occ:path:study",
      nodeId: organization,
      depth: 1,
      parentOccurrenceId: "occ:root",
      viaFactId: "f:study",
      direction: "outgoing",
      state: "expanded",
    },
    components: [
      {
        kind: "textBlock",
        id: "text:path:study",
        text: "Первый смысловой путь к тому же узлу.",
      },
    ],
  };

  const secondOccurrence: SectionComponent = {
    kind: "section",
    id: "section:path:work",
    title: "Связь через работу",
    presentation: "collapsed",
    occurrence: {
      occurrenceId: "occ:path:work",
      nodeId: organization,
      depth: 1,
      parentOccurrenceId: "occ:root",
      viaFactId: "f:work",
      direction: "outgoing",
      state: "cycle_reference",
    },
    components: [
      {
        kind: "textBlock",
        id: "text:path:work",
        text: "Второй смысловой путь к тому же узлу.",
      },
    ],
  };

  return {
    schemaVersion: "0.1",
    epoch: 0,
    revision: 0,
    context: { kind: "entity", entityId: person },
    diagnostics: [
      {
        kind: "diagnostic",
        id: "diagnostic:page",
        severity: "warning",
        message: "Страница содержит экспериментальную связь.",
      },
    ],
    page: {
      kind: "page",
      id: "page:alex",
      title: "Алексей",
      sections: [
        {
          kind: "section",
          id: "section:normal",
          title: "Сведения",
          presentation: "default",
          components: [
            {
              kind: "property",
              id: "property:unknown",
              predicate: unknownPredicate,
              label: "unclassified-42",
              direction: "outgoing",
              values: [
                {
                  kind: "text",
                  text: "Значение неизвестного предиката",
                  literalKind: "language",
                  language: "ru",
                  datatype: null,
                  editable: true,
                  source: source(
                    "f:unknown",
                    person,
                    unknownPredicate,
                    {
                      kind: "literal",
                      lexical: "Значение неизвестного предиката",
                      literalKind: "language",
                      language: "ru",
                      datatype: null,
                    },
                  ),
                },
              ],
            },
            {
              kind: "property",
              id: "property:incoming",
              predicate: "urn:logiclens:predicate:member",
              label: "Участники",
              direction: "incoming",
              values: [
                {
                  kind: "resourceLink",
                  targetId: organization,
                  label: "ИСИ СО РАН",
                  editable: false,
                  source: source(
                    "f:incoming",
                    organization,
                    "urn:logiclens:predicate:member",
                    { kind: "iri", resourceId: person },
                  ),
                },
              ],
            },
            {
              kind: "property",
              id: "property:derived",
              predicate: "urn:logiclens:predicate:summary",
              label: "Вывод",
              direction: "derived",
              values: [
                {
                  kind: "text",
                  text: "Связан с научной организацией",
                  literalKind: "plain",
                  language: null,
                  datatype: null,
                  editable: false,
                  source: {
                    kind: "derived",
                    ruleId: "rule:scientific-organization",
                    evidenceFactIds: ["f:study", "f:work"],
                  },
                },
              ],
            },
            firstOccurrence,
            secondOccurrence,
          ],
        },
        {
          kind: "section",
          id: "section:technical",
          title: "Технические данные",
          presentation: "technical",
          components: [
            {
              kind: "rawProlog",
              id: "raw:entity",
              title: "Фрагмент Prolog",
              artifactKind: "data",
              code: "fact('f:1', '<script>', p, literal('&', plain)).",
            },
          ],
        },
      ],
    },
  };
}

describe("UiDocumentRenderer", () => {
  it("renders every v0 component without domain-specific branches", () => {
    const html = renderToStaticMarkup(
      <UiDocumentRenderer document={fixture()} />,
    );

    expect(html).toContain("Алексей");
    expect(html).toContain("Значение неизвестного предиката");
    expect(html).toContain('data-direction="outgoing"');
    expect(html).toContain('data-direction="incoming"');
    expect(html).toContain("Исходящая связь");
    expect(html).toContain("Входящая связь");
    expect(html).toContain("Изменяемое");
    expect(html).toContain("Вычислено, только чтение");
    expect(html).toContain(
      'href="/entities/urn%3Alogiclens%3Aorganization%3Aisi"',
    );
    expect(html).toContain('data-occurrence-id="occ:path:study"');
    expect(html).toContain('data-occurrence-id="occ:path:work"');
    expect(html).toContain("ссылка на цикл");
  });

  it("keeps technical sections collapsed and renders Prolog as escaped text", () => {
    const html = renderToStaticMarkup(
      <UiDocumentRenderer document={fixture()} />,
    );

    expect(html).toContain('data-presentation="technical"');
    expect(html).not.toContain('<details open=""');
    expect(html).toContain("&lt;script&gt;");
    expect(html).toContain("&amp;");
    expect(html).not.toContain("<script>");
  });

  it("contains a damaged component and preserves page diagnostics", () => {
    const document = fixture();
    const normal = document.page.sections[0];
    if (normal === undefined) {
      throw new Error("Fixture normal section is missing.");
    }

    normal.components.splice(
      1,
      0,
      {
        kind: "property",
        id: "property:damaged",
        predicate: "urn:logiclens:predicate:damaged",
        label: "Повреждённое свойство",
        direction: "outgoing",
        values: null,
      } as unknown as SectionComponent,
    );

    const html = renderToStaticMarkup(
      <UiDocumentRenderer document={document} />,
    );

    expect(html).toContain(
      "Компонент не удалось отобразить. Остальная страница сохранена.",
    );
    expect(html).toContain("Страница содержит экспериментальную связь.");
    expect(html).toContain("Значение неизвестного предиката");
  });

  it("turns an unknown component kind into a local diagnostic", () => {
    const document = fixture();
    const normal = document.page.sections[0];
    if (normal === undefined) {
      throw new Error("Fixture normal section is missing.");
    }

    normal.components.push({
      kind: "timeline",
      id: "unsupported:timeline",
      events: [],
    } as unknown as SectionComponent);

    const html = renderToStaticMarkup(
      <UiDocumentRenderer document={document} />,
    );

    expect(html).toContain(
      "Компонент kind &#x27;timeline&#x27; не поддерживается UI Document v0.",
    );
    expect(html).toContain('data-diagnostic-scope="component"');
  });
});
