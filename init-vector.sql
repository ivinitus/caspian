-- Ensure pgvector extension is created
CREATE EXTENSION IF NOT EXISTS vector;

-- Check that the extension was successfully created
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
    RAISE EXCEPTION 'Vector extension could not be created';
  END IF;
END
$$;
