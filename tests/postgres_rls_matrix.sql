-- Run against a disposable CI database, never production.
-- Check every tenant-scoped relation using a NON-owner role (table owners bypass RLS).
BEGIN;
DO $setup$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='erp_rls_matrix_test') THEN
   CREATE ROLE erp_rls_matrix_test NOLOGIN;
 END IF;
END $setup$;
GRANT USAGE ON SCHEMA public TO erp_rls_matrix_test;
DO $grant$
DECLARE t record;
BEGIN
 FOR t IN SELECT DISTINCT table_name FROM information_schema.columns
          WHERE table_schema='public' AND column_name='tenant_id'
 LOOP
   EXECUTE format('GRANT SELECT ON TABLE public.%I TO erp_rls_matrix_test',t.table_name);
 END LOOP;
END $grant$;
CREATE TEMP TABLE rls_matrix_result(table_name text, missing_scope bigint, demo_visible bigint, other_visible bigint, wrong_scope bigint);
SET LOCAL ROLE erp_rls_matrix_test;
DO $verify$
DECLARE t record; missing bigint; demo bigint; other_tenant bigint; wrong bigint;
BEGIN
 FOR t IN SELECT DISTINCT table_name FROM information_schema.columns
          WHERE table_schema='public' AND column_name='tenant_id'
          AND table_name NOT IN ('members','invites','auth_sessions')
 LOOP
   PERFORM set_config('erp.tenant_id','',true);
   EXECUTE format('SELECT count(*) FROM public.%I',t.table_name) INTO missing;
   PERFORM set_config('erp.tenant_id','demo-erp-tenant-2026',true);
   EXECUTE format('SELECT count(*) FROM public.%I',t.table_name) INTO demo;
   EXECUTE format('SELECT count(*) FROM public.%I WHERE tenant_id <> %L',
                  t.table_name,'demo-erp-tenant-2026') INTO wrong;
   PERFORM set_config('erp.tenant_id','ci-other-tenant',true);
   EXECUTE format('SELECT count(*) FROM public.%I',t.table_name) INTO other_tenant;
   IF missing <> 0 OR wrong <> 0 THEN
     RAISE EXCEPTION 'Tenant RLS leak: table %, missing_scope %, wrong_scope %',
                     t.table_name,missing,wrong;
   END IF;
   INSERT INTO pg_temp.rls_matrix_result VALUES(t.table_name,missing,demo,other_tenant,wrong);
 END LOOP;
END $verify$;
RESET ROLE;
DO $assert$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM pg_temp.rls_matrix_result;
 IF n < 30 THEN RAISE EXCEPTION 'RLS coverage unexpectedly small: %',n; END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_temp.rls_matrix_result
               WHERE table_name='products' AND demo_visible >= 416) THEN
   RAISE EXCEPTION 'Demo product RLS visibility regression';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_temp.rls_matrix_result
               WHERE table_name='categories' AND other_visible >= 1) THEN
   RAISE EXCEPTION 'Other tenant baseline missing';
 END IF;
 RAISE NOTICE 'Tenant isolation matrix PASS: % tenant-scoped tables tested',n;
END $assert$;
ROLLBACK;
