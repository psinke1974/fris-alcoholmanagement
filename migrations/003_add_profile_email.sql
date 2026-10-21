-- Voeg e-mailadres toe aan profielen (voor wachtwoordherstel)
ALTER TABLE profiles ADD COLUMN email VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email) WHERE email IS NOT NULL;
