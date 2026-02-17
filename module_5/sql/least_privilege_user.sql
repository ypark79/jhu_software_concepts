-- Step 3: Least-privilege DB user for Grad Cafe Analytics
-- Run as PostgreSQL superuser. Replace YOUR_DATABASE_NAME and CHANGE_ME.
-- To run: psql -d YOUR_DATABASE_NAME -f least_privilege_user.sql

-- 1. Create the role (use a strong password; do not commit real passwords)
CREATE ROLE gradcafe_app WITH LOGIN PASSWORD 'CHANGE_ME' NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- 2. Grant CONNECT on the database
GRANT CONNECT ON DATABASE "YOUR_DATABASE_NAME" TO gradcafe_app;

-- 3. Grant USAGE on schema and privileges on applicants (run when connected to YOUR_DATABASE_NAME)
--    If running from postgres DB, connect to your DB first, then run steps 3-4.
GRANT USAGE ON SCHEMA public TO gradcafe_app;

-- 4. Permissions granted and why:
--    SELECT  - app.py and query_data.py read analysis data
--    INSERT  - load_data.py and clean.py insert rows
--    UPDATE  - clean.py uses ON CONFLICT DO UPDATE for upserts
--    TRUNCATE - load_data.py truncates before loading JSON
--    No DROP, ALTER, or owner-level permissions. Role is not a superuser.
GRANT SELECT, INSERT, UPDATE, TRUNCATE ON TABLE applicants TO gradcafe_app;
