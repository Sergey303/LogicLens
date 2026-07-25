export type Direction = "outgoing" | "incoming" | "derived";
export type Presentation = "default" | "collapsed" | "technical";
export type Severity = "info" | "warning" | "error";

export interface UiDocument {
  schemaVersion: "0.1";
  epoch: number;
  revision: number;
  context:
    | { kind: "entity"; entityId: string }
    | { kind: "query"; requestId: string };
  page: PageComponent;
  diagnostics: DiagnosticComponent[];
}

export interface PageComponent {
  kind: "page";
  id: string;
  title: string;
  sections: SectionComponent[];
}

export interface SectionComponent {
  kind: "section";
  id: string;
  title: string;
  presentation: Presentation;
  occurrence?: OccurrenceContext;
  components: UiComponent[];
}

export interface OccurrenceContext {
  occurrenceId: string;
  nodeId: string;
  depth: number;
  parentOccurrenceId: string | null;
  viaFactId: string | null;
  direction: "root" | "outgoing" | "incoming";
  state: "expanded" | "boundary" | "cycle_reference" | "limited";
}

export type UiComponent =
  | SectionComponent
  | PropertyComponent
  | TextBlockComponent
  | RawPrologComponent
  | DiagnosticComponent;

export interface PropertyComponent {
  kind: "property";
  id: string;
  predicate: string;
  label: string;
  direction: Direction;
  values: UiValue[];
}

export type UiValue = TextValue | ResourceLinkValue;

export interface TextValue {
  kind: "text";
  text: string;
  literalKind: "plain" | "language" | "datatype";
  language: string | null;
  datatype: string | null;
  editable: boolean;
  source: ValueSource;
}

export interface ResourceLinkValue {
  kind: "resourceLink";
  targetId: string;
  label: string;
  editable: boolean;
  source: ValueSource;
}

export type ValueSource = BaseSource | DerivedSource;

export interface BaseSource {
  kind: "base";
  fact: CanonicalFact;
  origins: string[];
}

export interface DerivedSource {
  kind: "derived";
  ruleId: string;
  evidenceFactIds: string[];
}

export interface CanonicalFact {
  factId: string;
  subject: string;
  predicate: string;
  object:
    | { kind: "iri"; resourceId: string }
    | {
        kind: "literal";
        lexical: string;
        literalKind: "plain" | "language" | "datatype";
        language: string | null;
        datatype: string | null;
      };
}

export interface TextBlockComponent {
  kind: "textBlock";
  id: string;
  text: string;
  source?: ValueSource;
}

export interface RawPrologComponent {
  kind: "rawProlog";
  id: string;
  title: string;
  code: string;
  artifactKind: "query" | "data" | "view" | "rule" | "diagnostic";
}

export interface DiagnosticComponent {
  kind: "diagnostic";
  id: string;
  severity: Severity;
  message: string;
}
