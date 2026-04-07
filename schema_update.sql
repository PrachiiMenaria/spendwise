-- Database Schema Fixes
-- Run these in your PostgreSQL terminal or pgAdmin

-- 1. Ensure goals tracking and deadlines are supported
ALTER TABLE goals ADD COLUMN IF NOT EXISTS target_amount FLOAT DEFAULT 0;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS saved_amount FLOAT DEFAULT 0;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS deadline DATE;

-- 2. Ensure CPW tracking columns exist
ALTER TABLE wardrobe_items ADD COLUMN IF NOT EXISTS purchase_price FLOAT DEFAULT 0;
ALTER TABLE wardrobe_items ADD COLUMN IF NOT EXISTS wear_count INTEGER DEFAULT 0;
ALTER TABLE wardrobe_items ADD COLUMN IF NOT EXISTS last_worn DATE;
ALTER TABLE wardrobe_items ADD COLUMN IF NOT EXISTS tags VARCHAR(255);

-- 3. Ensure the User configuration allows budget tracking
ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_budget FLOAT DEFAULT 0;
