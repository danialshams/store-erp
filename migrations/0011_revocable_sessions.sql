-- 0011: hashed throttle keys, revocable sessions. Do not expose session identifiers publicly.
BEGIN;
CREATE TABLE IF NOT EXISTS auth_sessions (
 id VARCHAR(36) PRIMARY KEY,tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
 created_at TIMESTAMPTZ NOT NULL,jti VARCHAR(80) NOT NULL UNIQUE,
 user_id VARCHAR(36) NOT NULL REFERENCES users(id),expires_at TIMESTAMPTZ NOT NULL,
 revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_auth_sessions_tenant_id ON auth_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
CREATE TABLE IF NOT EXISTS login_throttles (
 key VARCHAR(64) PRIMARY KEY,attempts INTEGER NOT NULL DEFAULT 0,
 window_start TIMESTAMPTZ NOT NULL,blocked_until TIMESTAMPTZ
);
DO $$
BEGIN
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='store_erp_app_rw') THEN
  EXECUTE 'GRANT SELECT,INSERT,UPDATE,DELETE ON public.auth_sessions,public.login_throttles TO store_erp_app_rw';
 END IF;
END $$;
COMMIT;
