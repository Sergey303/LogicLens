DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'relational_cmp_reader') THEN
        CREATE ROLE relational_cmp_reader NOLOGIN;
    END IF;
END
$$;

REVOKE ALL ON SCHEMA relational_cmp FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA relational_cmp FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA relational_cmp FROM PUBLIC;
GRANT USAGE ON SCHEMA relational_cmp TO relational_cmp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA relational_cmp TO relational_cmp_reader;
GRANT EXECUTE ON FUNCTION relational_cmp.resolve_claim(text, text, text) TO relational_cmp_reader;
