import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import type { UiDocument } from "../model/uiDocument";
import { UiDocumentRenderer } from "./UiDocumentRenderer";

it("renders a depth-two occurrence hierarchy without a domain component", () => {
  const document: UiDocument = {
    schemaVersion: "0.1",
    epoch: 0,
    revision: 0,
    context: {
      kind: "entity",
      entityId: "urn:logiclens:entity:root",
    },
    diagnostics: [],
    page: {
      kind: "page",
      id: "page:root",
      title: "Корневая сущность",
      sections: [
        {
          kind: "section",
          id: "section:root",
          title: "Подграф",
          presentation: "default",
          occurrence: {
            occurrenceId: "occ:root",
            nodeId: "urn:logiclens:entity:root",
            depth: 0,
            parentOccurrenceId: null,
            viaFactId: null,
            direction: "root",
            state: "expanded",
          },
          components: [
            {
              kind: "section",
              id: "section:depth-1",
              title: "Уровень 1",
              presentation: "collapsed",
              occurrence: {
                occurrenceId: "occ:depth-1",
                nodeId: "urn:logiclens:entity:shared",
                depth: 1,
                parentOccurrenceId: "occ:root",
                viaFactId: "f:depth-1",
                direction: "outgoing",
                state: "expanded",
              },
              components: [
                {
                  kind: "section",
                  id: "section:depth-2",
                  title: "Уровень 2",
                  presentation: "collapsed",
                  occurrence: {
                    occurrenceId: "occ:depth-2",
                    nodeId: "urn:logiclens:entity:shared",
                    depth: 2,
                    parentOccurrenceId: "occ:depth-1",
                    viaFactId: "f:depth-2",
                    direction: "incoming",
                    state: "cycle_reference",
                  },
                  components: [
                    {
                      kind: "textBlock",
                      id: "text:depth-2",
                      text: "Один renderer сохранил второй путь и цикл.",
                    },
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
  };

  const html = renderToStaticMarkup(
    <UiDocumentRenderer document={document} />,
  );

  expect(html).toContain('data-nesting-depth="0"');
  expect(html).toContain('data-nesting-depth="1"');
  expect(html).toContain('data-nesting-depth="2"');
  expect(html).toContain('data-occurrence-id="occ:root"');
  expect(html).toContain('data-occurrence-id="occ:depth-1"');
  expect(html).toContain('data-occurrence-id="occ:depth-2"');
  expect(html).toContain("Один renderer сохранил второй путь и цикл.");
  expect(html).toContain("ссылка на цикл");
});
