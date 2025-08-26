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

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding VECTOR(1536) -- adjust dimension as needed
);

-- Insert a new conversation record
INSERT INTO conversations (started_at)
VALUES (NOW())
RETURNING id;

