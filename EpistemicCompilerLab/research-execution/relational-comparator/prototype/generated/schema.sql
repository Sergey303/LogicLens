CREATE SCHEMA IF NOT EXISTS relational_cmp;

CREATE TABLE relational_cmp.proposition (
    proposition_id text PRIMARY KEY,
    subject_text text NOT NULL,
    predicate_text text NOT NULL,
    object_text text NOT NULL
);

CREATE TABLE relational_cmp.source_assertion (
    assertion_id text PRIMARY KEY,
    proposition_id text NOT NULL REFERENCES relational_cmp.proposition(proposition_id),
    polarity text NOT NULL CHECK (polarity IN ('positive', 'negative')),
    scope_id text NOT NULL,
    version_text text NOT NULL,
    source_id text NOT NULL
);

CREATE TABLE relational_cmp.strict_implication (
    rule_id text PRIMARY KEY,
    antecedent_proposition_id text NOT NULL REFERENCES relational_cmp.proposition(proposition_id),
    consequent_proposition_id text NOT NULL REFERENCES relational_cmp.proposition(proposition_id),
    scope_id text NOT NULL,
    version_text text NOT NULL
);

CREATE OR REPLACE FUNCTION relational_cmp.resolve_claim(
    p_proposition_id text,
    p_scope_id text,
    p_version text
)
RETURNS TABLE (
    status_code text,
    action_code text,
    evidence text[],
    provenance text[]
)
LANGUAGE sql
STABLE
SECURITY INVOKER
AS $$
WITH RECURSIVE positive_reach(proposition_id, assertion_id, source_id, rule_path) AS (
    SELECT a.proposition_id, a.assertion_id, a.source_id, ARRAY[]::text[]
    FROM relational_cmp.source_assertion a
    WHERE a.polarity = 'positive'
      AND a.scope_id = p_scope_id
      AND a.version_text = p_version
    UNION
    SELECT r.consequent_proposition_id, pr.assertion_id, pr.source_id, pr.rule_path || r.rule_id
    FROM positive_reach pr
    JOIN relational_cmp.strict_implication r
      ON r.antecedent_proposition_id = pr.proposition_id
     AND r.scope_id = p_scope_id
     AND r.version_text = p_version
    WHERE NOT r.rule_id = ANY(pr.rule_path)
),
pos AS (
    SELECT DISTINCT assertion_id, source_id
    FROM positive_reach
    WHERE proposition_id = p_proposition_id
),
neg AS (
    SELECT DISTINCT a.assertion_id, a.source_id
    FROM relational_cmp.source_assertion a
    WHERE a.proposition_id = p_proposition_id
      AND a.polarity = 'negative'
      AND a.scope_id = p_scope_id
      AND a.version_text = p_version
),
flags AS (
    SELECT EXISTS (SELECT 1 FROM pos) AS has_positive,
           EXISTS (SELECT 1 FROM neg) AS has_negative
),
classified AS (
    SELECT CASE
             WHEN has_positive AND has_negative THEN 'conflicting'
             WHEN has_positive THEN 'supported'
             WHEN has_negative THEN 'refuted'
             ELSE 'unknown'
           END AS status_code
    FROM flags
),
evidence_rows AS (
    SELECT assertion_id, source_id FROM pos
    UNION
    SELECT assertion_id, source_id FROM neg
)
SELECT c.status_code,
       CASE c.status_code
         WHEN 'supported' THEN 'accept'
         WHEN 'refuted' THEN 'reject'
         ELSE 'review'
       END AS action_code,
       COALESCE((SELECT array_agg(assertion_id ORDER BY assertion_id) FROM evidence_rows), ARRAY[]::text[]) AS evidence,
       COALESCE((SELECT array_agg(DISTINCT source_id ORDER BY source_id) FROM evidence_rows), ARRAY[]::text[]) AS provenance
FROM classified c;
$$;
