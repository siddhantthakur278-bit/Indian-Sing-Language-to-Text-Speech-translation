# Sanket Database Layer: PostgreSQL & psql Integration Guide

This directory contains production-ready PostgreSQL DDL and psql query files for the **Sanket Indian Sign Language (ISL)** platform.

---

## 1. Files in this Directory

| File | Purpose |
|---|---|
| `schema.sql` | Full PostgreSQL DDL: tables (`users`, `translation_records`, `saved_phrases`, `practice_sessions`, `emergency_alerts`), custom ENUMs, foreign keys, cascading rules, JSONB GIN indexes, partial indexes, and automatic timestamp update triggers. |
| `queries.sql` | Production SQL query suite for `psql`: seeding idempotent records, user profile management, cursor pagination, JSONB `@>` gloss searches, keyboard shortcut resolution, streak calculation using window functions, and analytics. |

---

## 2. Prerequisites

- PostgreSQL 14+ installed locally or on cloud (Supabase, Neon, AWS RDS, Render PostgreSQL).
- Standard `psql` command-line utility.

---

## 3. How to Execute with `psql`

### Step 1: Create Database
```bash
# Connect as postgres admin and create the database
psql -U postgres -d postgres -c "CREATE DATABASE isl_translator;"
```

### Step 2: Initialize Schema
```bash
# Apply tables, types, triggers, and indexes
psql -U postgres -d isl_translator -f database/schema.sql
```

### Step 3: Run Queries and Seeds
```bash
# Run seed data insertion and execute diagnostic/analytical queries
psql -U postgres -d isl_translator -f database/queries.sql
```

### Step 4: Interactive Inspection in `psql`
```bash
psql -U postgres -d isl_translator

# Inside psql terminal:
\dt                  -- List all tables
\d translation_records -- Describe table schema and indexes
\i database/queries.sql -- Execute queries script interactively
```

---

## 4. Environment Configuration

When switching the backend or web application from SQLite to PostgreSQL:

In `.env`:
```env
DATABASE_URL="postgresql://postgres:password@localhost:5432/isl_translator?schema=public"
```

In `render.yaml` (if provisioning managed Render PostgreSQL):
```yaml
databases:
  - name: isl-db
    databaseName: isl_translator
    user: isl_admin
    plan: free
```
