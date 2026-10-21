-- Tijdelijke demo-accounts (alleen gebruikt als DEMO_MODE aan staat)
ALTER TABLE users ADD COLUMN demo_expires_at DATETIME;
CREATE INDEX IF NOT EXISTS ix_users_demo_expires_at ON users(demo_expires_at);
