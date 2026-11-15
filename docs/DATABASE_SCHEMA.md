# ISL Translator: Prisma Database Architecture

## 1. Overview
The database layer is managed using **Prisma ORM** (`v5.22.0`) with **SQLite** (`dev.db`). It provides lightweight, reliable, zero-config local persistence ensuring that:
1. All video and landmark tracking remains **100% on-device** (never uploaded to any server or cloud).
2. Users can customize their assistive profiles, bookmark critical communication phrases, review translation history, and track practice session progress offline.

---

## 2. Entity-Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ TRANSLATION_RECORD : logs
    USER ||--o{ SAVED_PHRASE : bookmarks
    USER ||--o{ PRACTICE_SESSION : records
    USER o|--o{ EMERGENCY_ALERT : triggers
    TRANSLATION_RECORD o|--o{ EMERGENCY_ALERT : produces

    USER {
        string id PK "cuid"
        string name "Signer / User name"
        string email UK "Optional email"
        string avatarUrl "Optional profile image URL"
        string role "Signer | Interpreter | Learner"
        string preferredLang "en, hi, mr, etc."
        float speechRate "TTS playback speed (0.75x - 1.5x)"
        boolean autoSpeak "Play TTS automatically"
        string signMode "auto | hold"
        string theme "galaxy-gold | high-contrast"
        datetime createdAt
        datetime updatedAt
    }

    TRANSLATION_RECORD {
        string id PK "cuid"
        string userId FK
        string glosses "JSON string array e.g. ['ME', 'HOSPITAL']"
        string english "Reconstructed English sentence"
        string translated "Translated Indian language text"
        string lang "Target language code"
        boolean isEmergency "True if SOS priority trigger"
        string audioUrl "Optional cloud TTS audio URL"
        datetime createdAt
    }

    SAVED_PHRASE {
        string id PK "cuid"
        string userId FK
        string title "Short phrase label"
        string glosses "JSON string array"
        string english "English sentence"
        string translated "Target translation"
        string category "Emergency | Medical | Daily | Greetings | Travel"
        string shortcut "Optional single-key hotkey (e.g. H)"
        datetime createdAt
    }

    PRACTICE_SESSION {
        string id PK "cuid"
        string userId FK
        int signsRecognized "Number of signs verified"
        int durationSeconds "Drill practice time in seconds"
        float accuracy "Verification confidence percentage"
        string drillType "Fingerspelling | sign practice"
        datetime createdAt
    }

    EMERGENCY_ALERT {
        string id PK "cuid"
        string userId FK "Nullable"
        string translationId FK "Nullable"
        string alertType "Emergency category"
        string glossTrigger "Triggering gloss sequence"
        string dispatchedText "Fixed emergency message"
        string status "TRIGGERED | ACKNOWLEDGED | RESOLVED | CANCELLED"
        datetime acknowledgedAt "Nullable"
        datetime createdAt
    }
```

---

## 3. Database Management & Seeding Commands

### A. Local SQLite (Prisma ORM)
```bash
# Push schema changes to SQLite dev.db
npx prisma db push

# Generate Prisma Client
npx prisma generate

# Seed initial default user and curated emergency phrases
npm run db:seed

# Inspect database visually with Prisma Studio
npx prisma studio
```

### B. Production PostgreSQL via `psql` CLI
For centralized persistence on cloud providers (Render Postgres, Supabase, Neon):

```bash
# 1. Create database
psql -U postgres -d postgres -c "CREATE DATABASE isl_translator;"

# 2. Apply complete DDL schema, types, indexes, and triggers
psql -U postgres -d isl_translator -f database/schema.sql

# 3. Seed data and run query suite
psql -U postgres -d isl_translator -f database/queries.sql
```

See [database/README.md](file:///Users/siddhant/Downloads/asd_project_major/database/README.md) and [database/queries.sql](file:///Users/siddhant/Downloads/asd_project_major/database/queries.sql) for the complete psql query suite.
