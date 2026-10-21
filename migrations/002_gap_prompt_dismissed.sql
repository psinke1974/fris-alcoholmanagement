-- Voeg veld toe om overgeslagen inhaalperiodes te onthouden
ALTER TABLE users ADD COLUMN gap_prompt_dismissed_until DATE;
