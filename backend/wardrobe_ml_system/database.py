"""
Database Module for Wardrobe ML System.

Handles:
- PostgreSQL connection management
- Fetching user historical data
- Storing predictions
- Schema creation
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import pandas as pd
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from wardrobe_ml_system.ml_config import DB_CONFIG


class DatabaseManager:
    """
    Manages PostgreSQL connections and operations for the Wardrobe ML System.
    
    Uses connection pooling for efficient resource management.
    """
    
    def __init__(self, config: Dict[str, str] = None):
        """
        Initialize database manager with connection pool.
        
        Args:
            config: Database configuration dictionary
        """
        self.config = config or DB_CONFIG
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Create a connection pool for efficient database access."""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )
            print("Database connection pool initialized")
        except psycopg2.Error as e:
            print(f"Failed to create connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Automatically handles connection acquisition and release.
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def create_tables(self):
        """
        Create necessary database tables if they don't exist.
        
        Tables:
        - user_clothing_data: Stores user behavior metrics
        - predictions: Stores model predictions and alerts
        """
        create_user_data_table = """
        CREATE TABLE IF NOT EXISTS user_clothing_data (
            user_id SERIAL PRIMARY KEY,
            monthly_budget DECIMAL(10, 2) NOT NULL,
            total_clothing_spent_last_month DECIMAL(10, 2),
            number_of_purchases_last_month INTEGER,
            wardrobe_size INTEGER,
            total_times_worn INTEGER,
            average_decision_time_minutes DECIMAL(5, 2),
            shopping_frequency_per_month DECIMAL(4, 2),
            next_month_spending DECIMAL(10, 2),
            predicted_next_month_spending DECIMAL(10, 2),
            prediction_alert BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_predictions_table = """
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES user_clothing_data(user_id),
            predicted_spending DECIMAL(10, 2) NOT NULL,
            actual_spending DECIMAL(10, 2),
            alert_triggered BOOLEAN DEFAULT FALSE,
            alert_message TEXT,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_index = """
        CREATE INDEX IF NOT EXISTS idx_user_predictions 
        ON predictions(user_id, prediction_date DESC);
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_user_data_table)
                cur.execute(create_predictions_table)
                cur.execute(create_index)
                print("Database tables created successfully")
    
    def fetch_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch historical data for a specific user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dictionary with user data or None if not found
        """
        query = """
        SELECT 
            user_id,
            monthly_budget,
            total_clothing_spent_last_month,
            number_of_purchases_last_month,
            wardrobe_size,
            total_times_worn,
            average_decision_time_minutes,
            shopping_frequency_per_month
        FROM user_clothing_data
        WHERE user_id = %s;
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (user_id,))
                result = cur.fetchone()
                
                if result:
                    # Convert Decimal to float for ML processing
                    return {k: float(v) if v is not None else None 
                            for k, v in dict(result).items()}
                return None
    
    def fetch_all_users_data(self) -> pd.DataFrame:
        """
        Fetch all user data for model training.
        
        Returns:
            DataFrame with all user data
        """
        query = """
        SELECT 
            user_id,
            monthly_budget,
            total_clothing_spent_last_month,
            number_of_purchases_last_month,
            wardrobe_size,
            total_times_worn,
            average_decision_time_minutes,
            shopping_frequency_per_month,
            next_month_spending
        FROM user_clothing_data
        WHERE next_month_spending IS NOT NULL;
        """
        
        with self.get_connection() as conn:
            df = pd.read_sql(query, conn)
            print(f"Fetched {len(df)} user records for training")
            return df
    
    def store_prediction(
        self, 
        user_id: int, 
        predicted_spending: float,
        alert_triggered: bool = False,
        alert_message: str = None
    ) -> int:
        """
        Store a prediction result in the database.
        
        Args:
            user_id: The user's ID
            predicted_spending: The predicted amount
            alert_triggered: Whether spending alert was triggered
            alert_message: Optional alert message
            
        Returns:
            The prediction_id of the stored record
        """
        # Insert into predictions table
        insert_prediction = """
        INSERT INTO predictions 
            (user_id, predicted_spending, alert_triggered, alert_message)
        VALUES (%s, %s, %s, %s)
        RETURNING prediction_id;
        """
        
        # Update user's record with latest prediction
        update_user = """
        UPDATE user_clothing_data
        SET 
            predicted_next_month_spending = %s,
            prediction_alert = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s;
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Store prediction
                cur.execute(
                    insert_prediction, 
                    (user_id, predicted_spending, alert_triggered, alert_message)
                )
                prediction_id = cur.fetchone()[0]
                
                # Update user record
                cur.execute(
                    update_user,
                    (predicted_spending, alert_triggered, user_id)
                )
                
                print(f"Stored prediction {prediction_id} for user {user_id}")
                return prediction_id
    
    def get_user_prediction_history(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get prediction history for a user.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of records to return
            
        Returns:
            List of prediction records
        """
        query = """
        SELECT 
            prediction_id,
            predicted_spending,
            actual_spending,
            alert_triggered,
            prediction_date
        FROM predictions
        WHERE user_id = %s
        ORDER BY prediction_date DESC
        LIMIT %s;
        """
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (user_id, limit))
                results = cur.fetchall()
                return [dict(row) for row in results]
    
    def insert_sample_data(self, df: pd.DataFrame):
        """
        Insert sample data into the database for testing.
        
        Args:
            df: DataFrame with user data
        """
        insert_query = """
        INSERT INTO user_clothing_data (
            monthly_budget,
            total_clothing_spent_last_month,
            number_of_purchases_last_month,
            wardrobe_size,
            total_times_worn,
            average_decision_time_minutes,
            shopping_frequency_per_month,
            next_month_spending
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    cur.execute(insert_query, (
                        row["monthly_budget"],
                        row.get("total_clothing_spent_last_month"),
                        row.get("number_of_purchases_last_month"),
                        row.get("wardrobe_size"),
                        row.get("total_times_worn"),
                        row.get("average_decision_time_minutes"),
                        row.get("shopping_frequency_per_month"),
                        row.get("next_month_spending")
                    ))
                print(f"Inserted {len(df)} sample records")
    
    def close(self):
        """Close the connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("Database connection pool closed")


# Singleton instance for global access
_db_manager = None

def get_database() -> DatabaseManager:
    """Get or create the singleton database manager."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# Example usage
if __name__ == "__main__":
    from preprocessing import create_sample_data
    
    print("Testing Database Module...")
    
    try:
        db = get_database()
        
        # Create tables
        db.create_tables()
        
        # Generate and insert sample data
        sample_df = create_sample_data(100)
        db.insert_sample_data(sample_df)
        
        # Test fetching
        user_data = db.fetch_user_data(1)
        print(f"\nUser 1 data: {user_data}")
        
        # Test storing prediction
        prediction_id = db.store_prediction(
            user_id=1,
            predicted_spending=250.50,
            alert_triggered=True,
            alert_message="High spending predicted"
        )
        print(f"Created prediction: {prediction_id}")
        
        # Close connection
        db.close()
        
    except Exception as e:
        print(f"Database test failed: {e}")
        print("Make sure PostgreSQL is running and credentials are correct")
