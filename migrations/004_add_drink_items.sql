-- Bewaar individuele drankjes per registratie (JSON-array met id + count)
ALTER TABLE drink_logs ADD COLUMN drink_items TEXT;
