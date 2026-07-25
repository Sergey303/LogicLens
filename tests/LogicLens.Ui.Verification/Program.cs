using System.Text.Json.Nodes;
using LogicLens.Ui;
using LogicLens.Ui.Mapping;
using LogicLens.Ui.Validation;

namespace LogicLens.Ui.Verification;

internal static class Program
{
    private static async Task<int> Main(string[] args)
    {
        try
        {
            if (args.Length != 1 || string.IsNullOrWhiteSpace(args[0]))
            {
                throw new ArgumentException(
                    "Expected one argument: path to ui-document-v0.schema.json.");
            }

            var mapper = new GenericUiDocumentMapper();
            using var validator = new UiDocumentValidator(args[0]);
            var response = Fixture.EntityViewResponse();
            var facts = Fixture.Facts();
            var valid = mapper.MapEntityView(
                response,
                Fixture.Person,
                "ru");

            RequireValid(validator, valid, facts, "valid generic document");
            Equal(
                valid.ToJsonString(),
                mapper.MapEntityView(
                    Fixture.EntityViewResponse(),
                    Fixture.Person,
                    "ru").ToJsonString(),
                "generic mapping must be deterministic");

            var duplicate = Clone(valid);
            var duplicateSection = Sections(duplicate)[0]!.AsObject();
            duplicate["page"]!.AsObject()["id"] = duplicateSection["id"]!.DeepClone();
            RequireError(validator, duplicate, facts, "component_id");

            var mismatchedFact = Clone(valid);
            FirstValue(mismatchedFact)["source"]!
                .AsObject()["fact"]!
                .AsObject()["object"]!
                .AsObject()["lexical"] = "Подменено";
            RequireError(validator, mismatchedFact, facts, "fact_snapshot");

            var missingEvidence = Clone(valid);
            var derivedProperty = FirstProperty(missingEvidence);
            derivedProperty["direction"] = "derived";
            var derivedValue = FirstValue(missingEvidence);
            derivedValue["editable"] = false;
            derivedValue["source"] = new JsonObject
            {
                ["kind"] = "derived",
                ["ruleId"] = "rule:test",
                ["evidenceFactIds"] = new JsonArray("f:missing")
            };
            RequireError(validator, missingEvidence, facts, "evidence_fact");

            var activeMarkup = Clone(valid);
            activeMarkup["page"]!.AsObject()["title"] = "<script>alert(1)</script>";
            RequireError(validator, activeMarkup, facts, "active_markup");

            var executableTarget = Clone(valid);
            SecondProperty(executableTarget)["values"]!
                .AsArray()[0]!
                .AsObject()["targetId"] = "javascript:alert(1)";
            RequireError(validator, executableTarget, facts, "resource_scheme");

            var schemaInvalid = Clone(valid);
            FirstValue(schemaInvalid)["language"] = null;
            RequireError(validator, schemaInvalid, facts, "schema");

            using var limitedValidator = new UiDocumentValidator(
                args[0],
                new UiDocumentValidationOptions
                {
                    MaxComponents = 1,
                    MaxValues = 20_000,
                    MaxSectionDepth = 8,
                    MaxDocumentBytes = 2_000_000,
                    MaxErrors = 100
                });
            RequireError(
                limitedValidator,
                valid,
                facts,
                "component_count");

            var invalidSpecialized = Clone(valid);
            invalidSpecialized["page"]!
                .AsObject()["id"] = Sections(invalidSpecialized)[0]!
                .AsObject()["id"]!
                .DeepClone();
            var fallbackService = new UiDocumentService(
                mapper,
                validator,
                new InvalidSpecializedProvider(invalidSpecialized));
            var fallback = await fallbackService.BuildEntityDocumentAsync(
                Fixture.EntityViewResponse(),
                Fixture.Facts(),
                Fixture.Person,
                "ru",
                CancellationToken.None);
            RequireValid(validator, fallback, facts, "generic fallback document");
            var fallbackMessages = fallback["diagnostics"]!
                .AsArray()
                .Select(static item => item!
                    .AsObject()["message"]!
                    .GetValue<string>())
                .ToArray();
            Require(
                fallbackMessages.Contains(
                    "Специализированное представление отклонено; показано универсальное.",
                    StringComparer.Ordinal),
                "fallback diagnostic must be visible");

            Console.WriteLine("LogicLens.Ui verification passed.");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine("LogicLens.Ui verification failed.");
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    private static void RequireValid(
        IUiDocumentValidator validator,
        JsonObject document,
        JsonArray facts,
        string context)
    {
        var result = validator.Validate(document, facts, Fixture.Person);
        if (!result.IsValid)
        {
            throw new InvalidOperationException(
                $"{context}: {string.Join("; ", result.Errors)}");
        }
    }

    private static void RequireError(
        IUiDocumentValidator validator,
        JsonObject document,
        JsonArray facts,
        string code)
    {
        var result = validator.Validate(document, facts, Fixture.Person);
        if (!result.Errors.Any(error => StringComparer.Ordinal.Equals(
                error.Code,
                code)))
        {
            throw new InvalidOperationException(
                $"Expected validation error '{code}', actual: "
                + string.Join("; ", result.Errors));
        }
    }

    private static JsonObject Clone(JsonObject value) =>
        value.DeepClone().AsObject();

    private static JsonArray Sections(JsonObject document) =>
        document["page"]!.AsObject()["sections"]!.AsArray();

    private static JsonObject FirstProperty(JsonObject document) =>
        Sections(document)[0]!
            .AsObject()["components"]!
            .AsArray()[0]!
            .AsObject();

    private static JsonObject SecondProperty(JsonObject document) =>
        Sections(document)[0]!
            .AsObject()["components"]!
            .AsArray()[1]!
            .AsObject();

    private static JsonObject FirstValue(JsonObject document) =>
        FirstProperty(document)["values"]!
            .AsArray()[0]!
            .AsObject();

    private static void Equal<T>(T expected, T actual, string context)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
        {
            throw new InvalidOperationException(
                $"{context}: expected '{expected}', actual '{actual}'.");
        }
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }
}
