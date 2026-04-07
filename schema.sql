-- ============================================================
-- Finora / WardrobeIQ  –  PostgreSQL Schema
-- Run once on your database to set up all tables.
-- ============================================================

-- Users
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(120)  NOT NULL,
    email           VARCHAR(255)  NOT NULL UNIQUE,
    password_hash   TEXT          NOT NULL,
    monthly_budget  NUMERIC(12,2) DEFAULT 0,
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);

-- Expenses
CREATE TABLE IF NOT EXISTS expenses (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount          NUMERIC(12,2) NOT NULL,
    category        VARCHAR(80)   NOT NULL DEFAULT 'Others',
    expense_month   SMALLINT      NOT NULL,
    expense_year    SMALLINT      NOT NULL,
    note            TEXT          DEFAULT '',
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_expenses_user_month
    ON expenses(user_id, expense_year, expense_month);

-- Monthly budgets (overrides user default per month)
CREATE TABLE IF NOT EXISTS budgets (
    id      SERIAL PRIMARY KEY,
    user_id INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    year    SMALLINT      NOT NULL,
    month   SMALLINT      NOT NULL,
    amount  NUMERIC(12,2) NOT NULL,
    UNIQUE (user_id, year, month)
);

-- Wardrobe items
CREATE TABLE IF NOT EXISTS wardrobe_items (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_name       VARCHAR(150)  NOT NULL,
    category        VARCHAR(80),
    color           VARCHAR(60),
    purchase_price  NUMERIC(12,2) DEFAULT 0,
    wear_count      INTEGER       DEFAULT 0,
    created_at      TIMESTAMPTZ   DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wardrobe_user
    ON wardrobe_items(user_id);

-- Savings goals (optional – used by AI health score)
CREATE TABLE IF NOT EXISTS goals (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_name     VARCHAR(120)  NOT NULL,
    target_amount NUMERIC(12,2) NOT NULL,
    saved_amount  NUMERIC(12,2) DEFAULT 0,
    created_at    TIMESTAMPTZ   DEFAULT NOW()
);

-- ============================================================
-- Sample data (optional – remove in production)
-- ============================================================
-- INSERT INTO users(name, email, password_hash, monthly_budget)
-- VALUES('Demo User', 'demo@finora.app', 'hashed_password_here', 15000);