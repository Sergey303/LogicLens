using System.Text.Json.Nodes;
using LogicLens.Ui;

namespace LogicLens.Ui.Verification;

internal static class Fixture
{
    public const string Person = "urn:logiclens:person:test";

    public static JsonObject EntityViewResponse() => JsonNode.Parse(
        """
        {
          "protocolVersion": "0.1",
          "requestId": "fixture",
          "command": "entity-view",
          "status": "ok",
          "epoch": 0,
          "revision": 0,
          "result": {
            "kind": "entity-view",
            "entityId": "urn:logiclens:person:test",
            "effectiveLimits": {
              "maxFacts": 1000,
              "maxOutputBytes": 1000000,
              "timeoutMs": 2000
            },
            "view": {
              "kind": "entity_view",
              "entity": "urn:logiclens:person:test",
              "title": "Тестовый человек",
              "groups": [
                {
                  "direction": "outgoing",
                  "predicate": "urn:predicate:name",
                  "label": "Имя",
                  "priority": "01",
                  "technical": false,
                  "values": [
                    {
                      "kind": "text",
                      "text": "Иван",
                      "literalKind": "language",
                      "language": "ru",
                      "datatype": null,
                      "source": {
                        "kind": "base",
                        "factId": "f:name",
                        "subject": "urn:logiclens:person:test",
                        "predicate": "urn:predicate:name",
                        "object": {
                          "kind": "literal",
                          "lexical": "Иван",
                          "literalKind": "language",
                          "language": "ru",
                          "datatype": null
                        },
                        "origins": ["origin:name"]
                      }
                    }
                  ]
                },
                {
                  "direction": "incoming",
                  "predicate": "urn:predicate:participant",
                  "label": "Участие",
                  "priority": null,
                  "technical": false,
                  "values": [
                    {
                      "kind": "resourceLink",
                      "targetId": "urn:logiclens:membership:test",
                      "label": "Участие в организации",
                      "source": {
                        "kind": "base",
                        "factId": "f:participant",
                        "subject": "urn:logiclens:membership:test",
                        "predicate": "urn:predicate:participant",
                        "object": {
                          "kind": "iri",
                          "value": "urn:logiclens:person:test"
                        },
                        "origins": ["origin:participant"]
                      }
                    }
                  ]
                }
              ],
              "diagnostics": []
            },
            "rawProlog": "fact('f:name', 'urn:logiclens:person:test', 'urn:predicate:name', literal(\"Иван\", lang(ru))).\n"
          },
          "diagnostics": []
        }
        """)!.AsObject();

    public static JsonArray Facts() => JsonNode.Parse(
        """
        [
          {
            "factId": "f:name",
            "subject": "urn:logiclens:person:test",
            "predicate": "urn:predicate:name",
            "object": {
              "kind": "literal",
              "literalKind": "language",
              "lexical": "Иван",
              "language": "ru",
              "datatype": null
            },
            "origins": ["origin:name"]
          },
          {
            "factId": "f:participant",
            "subject": "urn:logiclens:membership:test",
            "predicate": "urn:predicate:participant",
            "object": {
              "kind": "iri",
              "value": "urn:logiclens:person:test"
            },
            "origins": ["origin:participant"]
          }
        ]
        """)!.AsArray();
}

internal sealed class InvalidSpecializedProvider(JsonObject invalid)
    : ISpecializedUiDocumentProvider
{
    public ValueTask<JsonObject?> TryBuildEntityDocumentAsync(
        JsonObject entityViewResponse,
        JsonArray authoritativeFacts,
        string entityId,
        string language,
        CancellationToken cancellationToken) =>
        ValueTask.FromResult<JsonObject?>(invalid.DeepClone().AsObject());
}
