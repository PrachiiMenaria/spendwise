-- Database Schema Fixes
-- Run these in your PostgreSQL terminal or pgAdmin

-- 1. Ensure goals tracking and deadlines are supported
ALTER TABLE goals ADD COLUMN IF NOT EXISTS target_amount FLOAT DEFAULT 0;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS saved_amount FLOAT DEFAULT 0;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS deadline DATE;

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

-- 3. Ensure the User configuration-- Make monthly_budget optional
ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_budget FLOAT DEFAULT NULL;
ALTER TABLE users ALTER COLUMN monthly_budget DROP NOT NULL;
ALTER TABLE users ALTER COLUMN monthly_budget SET DEFAULT NULL;

-- Track secure password reset links
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expiry TIMESTAMP;

-- Add mood column to expenses
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS mood VARCHAR(50);
