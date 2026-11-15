-- ============================================================================
-- SANKET: Indian Sign Language (ISL) Translation Platform
-- PostgreSQL Database DDL Schema (psql compatible)
-- ============================================================================
-- Description: Production PostgreSQL schema supporting user preferences,
--              real-time translation logs, JSONB gloss sequences, emergency
--              alerts, practice/drill analytics, and saved communication bookmarks.
--
-- Execution via psql:
--   psql -U postgres -d postgres -c "CREATE DATABASE isl_translator;"
--   psql -U postgres -d isl_translator -f database/schema.sql
-- ============================================================================

\set ON_ERROR_STOP on

-- Ensure required extensions are available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\echo 'Creating enum types and custom domains...'

-- Role enum
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
        CREATE TYPE user_role_enum AS ENUM ('Signer', 'Interpreter', 'Learner', 'Admin');
    END IF;
END $$;

-- Phrase category enum
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'phrase_category_enum') THEN
        CREATE TYPE phrase_category_enum AS ENUM ('Emergency', 'Medical', 'Greetings', 'Daily', 'Travel', 'General');
    END IF;
END $$;

-- Emergency alert status enum
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_status_enum') THEN
        CREATE TYPE alert_status_enum AS ENUM ('TRIGGERED', 'ACKNOWLEDGED', 'RESOLVED', 'CANCELLED');
    END IF;
END $$;

-- ============================================================================
-- 1. USERS & PROFILES TABLE
-- ============================================================================
\echo 'Creating table: users...'

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL DEFAULT 'Signer',
    email VARCHAR(255) UNIQUE,
    avatar_url TEXT,
    role user_role_enum NOT NULL DEFAULT 'Signer',
    preferred_lang VARCHAR(10) NOT NULL DEFAULT 'hi',
    speech_rate NUMERIC(3, 2) NOT NULL DEFAULT 1.00 CHECK (speech_rate >= 0.50 AND speech_rate <= 2.00),
    auto_speak BOOLEAN NOT NULL DEFAULT TRUE,
    sign_mode VARCHAR(20) NOT NULL DEFAULT 'auto' CHECK (sign_mode IN ('auto', 'hold')),
    theme VARCHAR(50) NOT NULL DEFAULT 'galaxy-gold',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. TRANSLATION RECORDS TABLE
-- ============================================================================
\echo 'Creating table: translation_records...'

CREATE TABLE IF NOT EXISTS translation_records (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    glosses JSONB NOT NULL,
    english TEXT NOT NULL,
    translated TEXT NOT NULL,
    lang VARCHAR(10) NOT NULL DEFAULT 'hi',
    is_emergency BOOLEAN NOT NULL DEFAULT FALSE,
    audio_url TEXT,
    inference_latency_ms INTEGER DEFAULT 0 CHECK (inference_latency_ms >= 0),
    client_ip INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. SAVED PHRASES / BOOKMARKS TABLE
-- ============================================================================
\echo 'Creating table: saved_phrases...'

CREATE TABLE IF NOT EXISTS saved_phrases (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    glosses JSONB NOT NULL,
    english TEXT NOT NULL,
    translated TEXT NOT NULL,
    category phrase_category_enum NOT NULL DEFAULT 'General',
    shortcut VARCHAR(10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. PRACTICE & DRILL SESSIONS TABLE
-- ============================================================================
\echo 'Creating table: practice_sessions...'

CREATE TABLE IF NOT EXISTS practice_sessions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    signs_recognized INTEGER NOT NULL DEFAULT 0 CHECK (signs_recognized >= 0),
    duration_seconds INTEGER NOT NULL DEFAULT 0 CHECK (duration_seconds >= 0),
    accuracy NUMERIC(5, 2) NOT NULL DEFAULT 0.00 CHECK (accuracy >= 0.00 AND accuracy <= 100.00),
    drill_type VARCHAR(50) NOT NULL DEFAULT 'fingerspelling',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. EMERGENCY AUDIT LOGS TABLE
-- ============================================================================
\echo 'Creating table: emergency_alerts...'

CREATE TABLE IF NOT EXISTS emergency_alerts (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    translation_id VARCHAR(36) REFERENCES translation_records(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    gloss_trigger TEXT NOT NULL,
    dispatched_text TEXT NOT NULL,
    status alert_status_enum NOT NULL DEFAULT 'TRIGGERED',
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. PERFORMANCE & SEARCH INDEXES
-- ============================================================================
\echo 'Creating performance and search indexes...'

-- User lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Translation lookups: user history & chronological sorting
CREATE INDEX IF NOT EXISTS idx_translations_user_created ON translation_records(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_translations_lang ON translation_records(lang);

-- Partial index for fast emergency querying
CREATE INDEX IF NOT EXISTS idx_translations_emergency ON translation_records(created_at DESC) WHERE is_emergency = TRUE;

-- GIN Index for fast JSONB search over gloss sequences (e.g. searching records containing 'HOSPITAL')
CREATE INDEX IF NOT EXISTS idx_translations_glosses_gin ON translation_records USING gin (glosses jsonb_path_ops);

-- Saved phrases: filter by user and category
CREATE INDEX IF NOT EXISTS idx_saved_phrases_user_category ON saved_phrases(user_id, category);

-- Unique index per user on hotkey shortcut (e.g. only one phrase can have hotkey 'H' per user)
CREATE UNIQUE INDEX IF NOT EXISTS uq_saved_phrases_user_shortcut ON saved_phrases(user_id, shortcut) WHERE shortcut IS NOT NULL;

-- Practice sessions: chronological drill tracking
CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_date ON practice_sessions(user_id, created_at DESC);

-- Emergency alerts lookup
CREATE INDEX IF NOT EXISTS idx_emergency_alerts_status ON emergency_alerts(status, created_at DESC);

-- ============================================================================
-- 7. AUTOMATED UPDATED_AT TIMESTAMP TRIGGER
-- ============================================================================
\echo 'Creating updated_at triggers...'

CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_timestamp_column();

DROP TRIGGER IF EXISTS trg_saved_phrases_updated_at ON saved_phrases;
CREATE TRIGGER trg_saved_phrases_updated_at
BEFORE UPDATE ON saved_phrases
FOR EACH ROW
EXECUTE FUNCTION update_timestamp_column();

\echo 'Sanket PostgreSQL Schema created successfully!'
