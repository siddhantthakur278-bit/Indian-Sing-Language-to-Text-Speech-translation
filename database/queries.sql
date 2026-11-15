-- ============================================================================
-- SANKET: Indian Sign Language (ISL) Translation Platform
-- Database Queries File for PostgreSQL / psql
-- ============================================================================
-- Description: Comprehensive, production-grade queries covering user management,
--              real-time translation logging, JSONB gloss searches, bookmark
--              shortcuts, practice drill statistics, and emergency auditing.
--
-- How to run this file via psql:
--   psql -U postgres -d isl_translator -f database/queries.sql
--   or interactively inside psql:
--   \i database/queries.sql
-- ============================================================================

\set ON_ERROR_STOP on
\echo '====================================================================='
-- Set display formatting for terminal output
\pset border 2
\pset format aligned

-- ============================================================================
-- SECTION 1: SEED DATA INITIALIZATION (IDEMPOTENT)
-- ============================================================================
\echo '>> Seeding initial user profiles...'

INSERT INTO users (id, name, email, role, preferred_lang, speech_rate, auto_speak, sign_mode, theme)
VALUES 
    ('usr_siddhant_01', 'Siddhant Thakur', 'siddhantthakur278@gmail.com', 'Signer', 'hi', 1.00, true, 'auto', 'galaxy-gold'),
    ('usr_parth_02',    'Parth Nayak',      'nayakparth2257@gmail.com',   'Interpreter', 'en', 1.10, true, 'auto', 'high-contrast'),
    ('usr_abhi_03',     'Abhishek Sharma',  'abhishek@isl-sanket.org',    'Learner', 'mr', 0.90, false, 'hold', 'galaxy-gold')
ON CONFLICT (email) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

\echo '>> Seeding standard emergency and daily bookmarks...'

INSERT INTO saved_phrases (id, user_id, title, glosses, english, translated, category, shortcut)
VALUES
    ('sp_seed_01', 'usr_siddhant_01', 'Need Hospital Immediately', '["ME", "HOSPITAL", "GO"]'::jsonb, 
     'I need to go to the hospital.', 'मुझे तुरंत अस्पताल जाना है।', 'Emergency', 'H'),
    ('sp_seed_02', 'usr_siddhant_01', 'Want Drinking Water', '["ME", "WATER", "WANT"]'::jsonb, 
     'I want water to drink.', 'मुझे पीने का पानी चाहिए।', 'Daily', 'W'),
    ('sp_seed_03', 'usr_siddhant_01', 'Please Help Me', '["PLEASE", "HELP", "ME"]'::jsonb, 
     'Please help me.', 'कृपया मेरी सहायता करें।', 'Emergency', 'P'),
    ('sp_seed_04', 'usr_siddhant_01', 'Hello Friend', '["HELLO", "FRIEND"]'::jsonb, 
     'Hello, friend.', 'नमस्ते दोस्त।', 'Greetings', 'G'),
    ('sp_seed_05', 'usr_siddhant_01', 'Severe Pain In Body', '["ME", "PAIN", "DOCTOR", "NEED"]'::jsonb, 
     'I have severe pain, I need a doctor.', 'मुझे बहुत दर्द हो रहा है, मुझे डॉक्टर चाहिए।', 'Medical', 'M')
ON CONFLICT DO NOTHING;

\echo '>> Seeding sample translation history...'

INSERT INTO translation_records (id, user_id, glosses, english, translated, lang, is_emergency, audio_url, inference_latency_ms, created_at)
VALUES
    ('tr_seed_01', 'usr_siddhant_01', '["HELLO"]'::jsonb, 
     'Hello!', 'नमस्ते!', 'hi', false, '/api/tts?text=%E0%A4%A8%E0%A4%AE%E0%A4%B8%E0%A5%8D%E0%A4%A4%E0%A5%87%21&lang=hi', 28, CURRENT_TIMESTAMP - INTERVAL '2 days'),
    ('tr_seed_02', 'usr_siddhant_01', '["THANK_YOU"]'::jsonb, 
     'Thank you very much.', 'धन्यवाद।', 'hi', false, null, 31, CURRENT_TIMESTAMP - INTERVAL '1 day 4 hours'),
    ('tr_seed_03', 'usr_siddhant_01', '["ME", "HOSPITAL", "GO"]'::jsonb, 
     'I am going to the hospital.', 'मी रुग्णालयात जात आहे.', 'mr', true, null, 42, CURRENT_TIMESTAMP - INTERVAL '6 hours'),
    ('tr_seed_04', 'usr_siddhant_01', '["YOU", "NAME", "WHAT"]'::jsonb, 
     'What is your name?', 'आपका नाम क्या है?', 'hi', false, null, 35, CURRENT_TIMESTAMP - INTERVAL '3 hours'),
    ('tr_seed_05', 'usr_siddhant_01', '["HELP", "POLICE"]'::jsonb, 
     'Please help! Call the police!', 'कृपया मदद करें! पुलिस को बुलाएं!', 'hi', true, null, 19, CURRENT_TIMESTAMP - INTERVAL '30 minutes')
ON CONFLICT DO NOTHING;

\echo '>> Seeding sample practice drill history...'

INSERT INTO practice_sessions (id, user_id, signs_recognized, duration_seconds, accuracy, drill_type, created_at)
VALUES
    ('ps_seed_01', 'usr_siddhant_01', 12, 180, 91.50, 'fingerspelling_az', CURRENT_TIMESTAMP - INTERVAL '3 days'),
    ('ps_seed_02', 'usr_siddhant_01', 15, 210, 94.20, 'fingerspelling_az', CURRENT_TIMESTAMP - INTERVAL '2 days'),
    ('ps_seed_03', 'usr_siddhant_01', 20, 240, 97.50, 'emergency_drills',  CURRENT_TIMESTAMP - INTERVAL '1 day'),
    ('ps_seed_04', 'usr_siddhant_01', 25, 300, 96.00, 'daily_vocabulary',   CURRENT_TIMESTAMP - INTERVAL '2 hours')
ON CONFLICT DO NOTHING;


-- ============================================================================
-- SECTION 2: USER & PROFILE MANAGEMENT QUERIES
-- ============================================================================
\echo ''
\echo '====================================================================='
\echo 'QUERY 2.1: Fetch User Profile and Preferences by Email'
\echo '====================================================================='

SELECT 
    id,
    name,
    email,
    role,
    preferred_lang,
    speech_rate,
    auto_speak,
    sign_mode,
    theme,
    created_at
FROM users
WHERE email = 'siddhantthakur278@gmail.com';

\echo ''
\echo '====================================================================='
\echo 'QUERY 2.2: Upsert User Preferences (Theme, Language, TTS Speed)'
\echo '====================================================================='

INSERT INTO users (id, name, email, preferred_lang, speech_rate, auto_speak, theme)
VALUES ('usr_siddhant_01', 'Siddhant Thakur', 'siddhantthakur278@gmail.com', 'hi', 1.15, true, 'galaxy-gold')
ON CONFLICT (id) DO UPDATE SET
    preferred_lang = EXCLUDED.preferred_lang,
    speech_rate    = EXCLUDED.speech_rate,
    auto_speak     = EXCLUDED.auto_speak,
    theme          = EXCLUDED.theme,
    updated_at     = CURRENT_TIMESTAMP
RETURNING id, name, preferred_lang, speech_rate, theme, updated_at;


-- ============================================================================
-- SECTION 3: TRANSLATION LOGGING & RETRIEVAL QUERIES
-- ============================================================================
\echo ''
\echo '====================================================================='
\echo 'QUERY 3.1: Insert Real-Time Recognized Translation Record'
\echo '====================================================================='

INSERT INTO translation_records (
    user_id,
    glosses,
    english,
    translated,
    lang,
    is_emergency,
    inference_latency_ms
) VALUES (
    'usr_siddhant_01',
    '["ME", "WATER", "DRINK", "WANT"]'::jsonb,
    'I want to drink water.',
    'मुझे पानी पीना है।',
    'hi',
    false,
    34
) RETURNING id, english, translated, lang, is_emergency, created_at;

\echo ''
\echo '====================================================================='
\echo 'QUERY 3.2: Retrieve Paginated Translation History for Active Signer'
\echo '====================================================================='

SELECT 
    tr.id,
    tr.glosses,
    tr.english,
    tr.translated,
    tr.lang,
    tr.is_emergency,
    tr.inference_latency_ms,
    TO_CHAR(tr.created_at, 'YYYY-MM-DD HH24:MI:SS') AS timestamp_formatted
FROM translation_records tr
WHERE tr.user_id = 'usr_siddhant_01'
ORDER BY tr.created_at DESC
LIMIT 10 OFFSET 0;

\echo ''
\echo '====================================================================='
\echo 'QUERY 3.3: High-Performance JSONB Search: Find Translations Containing Gloss "HOSPITAL"'
\echo '====================================================================='

SELECT 
    id,
    glosses,
    english,
    translated,
    is_emergency,
    created_at
FROM translation_records
WHERE glosses @> '["HOSPITAL"]'::jsonb
ORDER BY created_at DESC;

\echo ''
\echo '====================================================================='
\echo 'QUERY 3.4: Fetch Priority Emergency Trigger History'
\echo '====================================================================='

SELECT 
    tr.id,
    u.name AS signer_name,
    tr.glosses,
    tr.english,
    tr.translated,
    tr.created_at
FROM translation_records tr
LEFT JOIN users u ON tr.user_id = u.id
WHERE tr.is_emergency = TRUE
ORDER BY tr.created_at DESC;


-- ============================================================================
-- SECTION 4: SAVED PHRASES & QUICK HOTKEY BOOKMARKS
-- ============================================================================
\echo ''
\echo '====================================================================='
\echo 'QUERY 4.1: Retrieve All Bookmarked Phrases Grouped by Category'
\echo '====================================================================='

SELECT 
    category,
    title,
    shortcut,
    glosses,
    english,
    translated
FROM saved_phrases
WHERE user_id = 'usr_siddhant_01'
ORDER BY 
    CASE category
        WHEN 'Emergency' THEN 1
        WHEN 'Medical'   THEN 2
        WHEN 'Greetings' THEN 3
        WHEN 'Daily'     THEN 4
        ELSE 5
    END,
    title ASC;

\echo ''
\echo '====================================================================='
\echo 'QUERY 4.2: Fast Single-Key Shortcut Lookup (e.g. User presses key "H")'
\echo '====================================================================='

SELECT 
    id,
    title,
    glosses,
    english,
    translated,
    category
FROM saved_phrases
WHERE user_id = 'usr_siddhant_01' 
  AND UPPER(shortcut) = UPPER('H');

\echo ''
\echo '====================================================================='
\echo 'QUERY 4.3: Add or Replace a Custom Keyboard Shortcut Bookmark'
\echo '====================================================================='

INSERT INTO saved_phrases (user_id, title, glosses, english, translated, category, shortcut)
VALUES (
    'usr_siddhant_01',
    'Call An Ambulance',
    '["AMBULANCE", "CALL", "NEED"]'::jsonb,
    'Please call an ambulance immediately.',
    'कृपया तुरंत एम्बुलेंस को बुलाएं।',
    'Emergency',
    'A'
)
ON CONFLICT (user_id, shortcut) WHERE shortcut IS NOT NULL
DO UPDATE SET
    title       = EXCLUDED.title,
    glosses     = EXCLUDED.glosses,
    english     = EXCLUDED.english,
    translated  = EXCLUDED.translated,
    category    = EXCLUDED.category,
    updated_at  = CURRENT_TIMESTAMP
RETURNING id, title, shortcut, category;


-- ============================================================================
-- SECTION 5: PRACTICE DRILLS & GAMIFICATION ANALYTICS
-- ============================================================================
\echo ''
\echo '====================================================================='
\echo 'QUERY 5.1: Log Completed Practice Drill Session'
\echo '====================================================================='

INSERT INTO practice_sessions (
    user_id,
    signs_recognized,
    duration_seconds,
    accuracy,
    drill_type
) VALUES (
    'usr_siddhant_01',
    18,
    220,
    95.80,
    'fingerspelling_az'
) RETURNING id, signs_recognized, accuracy, duration_seconds, created_at;

\echo ''
\echo '====================================================================='
\echo 'QUERY 5.2: User Aggregated Practice Statistics Dashboard'
\echo '====================================================================='

SELECT 
    u.id AS user_id,
    u.name,
    COUNT(ps.id) AS total_sessions_completed,
    COALESCE(SUM(ps.signs_recognized), 0) AS total_signs_practiced,
    ROUND(COALESCE(AVG(ps.accuracy), 0)::numeric, 2) AS overall_avg_accuracy_percent,
    COALESCE(SUM(ps.duration_seconds), 0) / 60 AS total_practice_minutes,
    MAX(ps.created_at) AS last_practiced_at
FROM users u
LEFT JOIN practice_sessions ps ON u.id = ps.user_id
WHERE u.id = 'usr_siddhant_01'
GROUP BY u.id, u.name;

\echo ''
\echo '====================================================================='
\echo 'QUERY 5.3: Practice Consistency & Streak Calculation (Window Functions)'
\echo '====================================================================='

WITH daily_drills AS (
    SELECT DISTINCT
        user_id,
        DATE(created_at) AS drill_date
    FROM practice_sessions
    WHERE user_id = 'usr_siddhant_01'
),
streak_groups AS (
    SELECT 
        drill_date,
        drill_date - (DENSE_RANK() OVER (ORDER BY drill_date))::integer AS grp
    FROM daily_drills
)
SELECT 
    MIN(drill_date) AS streak_start,
    MAX(drill_date) AS streak_end,
    COUNT(*) AS consecutive_active_days
FROM streak_groups
GROUP BY grp
ORDER BY streak_end DESC
LIMIT 1;


-- ============================================================================
-- SECTION 6: BUSINESS INTELLIGENCE & RECOGNITION ANALYTICS
-- ============================================================================
\echo ''
\echo '====================================================================='
\echo 'QUERY 6.1: Top 10 Most Frequently Recognized Sign Glosses (Unnest JSONB)'
\echo '====================================================================='

SELECT 
    gloss_token,
    COUNT(*) AS frequency,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) AS percentage_of_total
FROM (
    SELECT jsonb_array_elements_text(glosses) AS gloss_token
    FROM translation_records
) t
GROUP BY gloss_token
ORDER BY frequency DESC
LIMIT 10;

\echo ''
\echo '====================================================================='
\echo 'QUERY 6.2: Translation Traffic Breakdown by Target Indian Language'
\echo '====================================================================='

SELECT 
    lang AS target_language_code,
    CASE lang
        WHEN 'hi' THEN 'Hindi (हिन्दी)'
        WHEN 'mr' THEN 'Marathi (मराठी)'
        WHEN 'en' THEN 'English'
        WHEN 'ta' THEN 'Tamil (தமிழ்)'
        WHEN 'te' THEN 'Telugu (తెలుగు)'
        WHEN 'bn' THEN 'Bengali (বাংলা)'
        WHEN 'gu' THEN 'Gujarati (ગુજરાતી)'
        WHEN 'kn' THEN 'Kannada (ಕನ್ನಡ)'
        WHEN 'ml' THEN 'Malayalam (മലയാളം)'
        WHEN 'pa' THEN 'Punjabi (ਪੰਜਾਬੀ)'
        ELSE 'Other'
    END AS language_name,
    COUNT(*) AS total_translations,
    COUNT(*) FILTER (WHERE is_emergency = TRUE) AS emergency_count,
    ROUND(AVG(inference_latency_ms), 1) AS avg_latency_ms
FROM translation_records
GROUP BY lang
ORDER BY total_translations DESC;

\echo ''
\echo '====================================================================='
\echo 'QUERY 6.3: System Latency Health Check & SLA Benchmark'
\echo '====================================================================='

SELECT 
    COUNT(*) AS total_sampled_requests,
    ROUND(AVG(inference_latency_ms), 2) AS mean_latency_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY inference_latency_ms) AS p50_median_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY inference_latency_ms) AS p95_latency_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY inference_latency_ms) AS p99_latency_ms,
    MAX(inference_latency_ms) AS max_latency_ms
FROM translation_records;

\echo ''
\echo '====================================================================='
\echo 'Sanket PostgreSQL queries executed successfully.'
\echo '====================================================================='
