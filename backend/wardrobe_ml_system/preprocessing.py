"""
Preprocessing Module for Wardrobe ML System.

Handles:
- Missing value imputation
- Outlier removal (IQR method)
- Feature engineering (computed columns)
- Feature scaling (StandardScaler)
- Train/test splitting
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os
from wardrobe_ml_system.ml_config import FEATURE_COLUMNS, SCALER_PATH


class DataPreprocessor:
    """
    Preprocesses raw user data for the spending prediction model.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = FEATURE_COLUMNS
        self.is_fitted = False
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values using appropriate strategies.
        
        Strategy:
        - Numerical columns: fill with median (robust to outliers)
        - Drop rows where target variable is missing
        
        Args:
            df: Raw dataframe with potential missing values
            
        Returns:
            DataFrame with missing values handled
        """
        df = df.copy()
        
        # Define numerical columns
        numerical_cols = [
            "monthly_budget",
            "total_clothing_spent_last_month",
            "number_of_purchases_last_month",
            "wardrobe_size",
            "total_times_worn",
            "average_decision_time_minutes",
            "shopping_frequency_per_month"
        ]
        
        # Fill missing numerical values with median
        for col in numerical_cols:
            if col in df.columns and df[col].isnull().any():
                median_value = df[col].median()
                df[col].fillna(median_value, inplace=True)
                print(f"Filled {col} missing values with median: {median_value:.2f}")
        
        # Drop rows where target is missing (only during training)
        if "next_month_spending" in df.columns:
            initial_rows = len(df)
            df.dropna(subset=["next_month_spending"], inplace=True)
            dropped = initial_rows - len(df)
            if dropped > 0:
                print(f"Dropped {dropped} rows with missing target values")
        
        return df
    
    def remove_outliers_iqr(self, df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
        """
        Remove outliers using the Interquartile Range (IQR) method.
        
        A value is considered an outlier if it falls below Q1 - 1.5*IQR
        or above Q3 + 1.5*IQR.
        
        Args:
            df: DataFrame to clean
            columns: Specific columns to check (defaults to all numerical)
            
        Returns:
            DataFrame with outliers removed
        """
        df = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude user_id from outlier detection
            columns = [c for c in columns if c != "user_id"]
        
        initial_rows = len(df)
        
        for col in columns:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # Filter out outliers
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        removed = initial_rows - len(df)
        print(f"Removed {removed} outlier rows ({removed/initial_rows*100:.1f}%)")
        
        return df
    
    def compute_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute derived features from raw data.
        
        Creates:
        - wardrobe_utilization_index: total_times_worn / wardrobe_size
        - spending_ratio: total_clothing_spent_last_month / monthly_budget
        
        Args:
            df: DataFrame with raw features
            
        Returns:
            DataFrame with additional computed features
        """
        df = df.copy()
        
        # Wardrobe utilization index: how often items are worn on average
        # Add small epsilon to avoid division by zero
        df["wardrobe_utilization_index"] = (
            df["total_times_worn"] / (df["wardrobe_size"] + 1e-6)
        )
        
        # Spending ratio: what fraction of budget was spent last month
        df["spending_ratio"] = (
            df["total_clothing_spent_last_month"] / (df["monthly_budget"] + 1e-6)
        )
        
        # Cap extreme values for stability
        df["wardrobe_utilization_index"] = df["wardrobe_utilization_index"].clip(0, 100)
        df["spending_ratio"] = df["spending_ratio"].clip(0, 10)
        
        print("Computed derived features: wardrobe_utilization_index, spending_ratio")
        
        return df
    
    def fit_scaler(self, df: pd.DataFrame) -> np.ndarray:
        """
        Fit the StandardScaler on training data and transform.
        
        Args:
            df: Training DataFrame with feature columns
            
        Returns:
            Scaled feature array
        """
        features = df[self.feature_columns].values
        scaled_features = self.scaler.fit_transform(features)
        self.is_fitted = True
        print(f"Fitted scaler on {len(df)} samples")
        return scaled_features
    
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transform features using the fitted scaler.
        
        Args:
            df: DataFrame with feature columns
            
        Returns:
            Scaled feature array
        """
        if not self.is_fitted:
            raise ValueError("Scaler not fitted. Call fit_scaler first or load a saved scaler.")
        
        features = df[self.feature_columns].values
        return self.scaler.transform(features)
    
    def preprocess_training_data(
        self, 
        df: pd.DataFrame, 
        remove_outliers: bool = True
    ) -> tuple:
        """
        Complete preprocessing pipeline for training data.
        
        Steps:
        1. Handle missing values
        2. Compute derived features
        3. Remove outliers (optional)
        4. Scale features
        5. Split into train/test
        
        Args:
            df: Raw training DataFrame
            remove_outliers: Whether to remove outliers
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test, preprocessed_df)
        """
        print("=" * 50)
        print("Starting preprocessing pipeline...")
        print("=" * 50)
        
        # Step 1: Handle missing values
        df = self.handle_missing_values(df)
        
        # Step 2: Compute derived features
        df = self.compute_derived_features(df)
        
        # Step 3: Remove outliers (optional)
        if remove_outliers:
            df = self.remove_outliers_iqr(df)
        
        # Step 4: Extract features and target
        X = df[self.feature_columns]
        y = df["next_month_spending"]
        
        # Step 5: Split data (80% train, 20% test)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"Split data: {len(X_train)} training, {len(X_test)} testing samples")
        
        # Step 6: Fit scaler on training data only
        X_train_scaled = self.fit_scaler(X_train)
        X_test_scaled = self.transform(X_test)
        
        print("Preprocessing complete!")
        print("=" * 50)
        
        return X_train_scaled, X_test_scaled, y_train.values, y_test.values, df
    
    def preprocess_single_input(self, input_dict: dict) -> np.ndarray:
        """
        Preprocess a single input for prediction.
        
        Computes derived features and scales the input.
        
        Args:
            input_dict: Dictionary with raw input values
            
        Returns:
            Scaled feature array ready for prediction
        """
        # Create single-row DataFrame
        df = pd.DataFrame([input_dict])
        
        # Compute derived features
        df = self.compute_derived_features(df)
        
        # Scale using fitted scaler
        return self.transform(df)
    
    def save_scaler(self, path: str = None):
        """Save the fitted scaler to disk."""
        path = path or SCALER_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.scaler, f)
        print(f"Scaler saved to {path}")
    
    def load_scaler(self, path: str = None):
        """Load a previously fitted scaler from disk."""
        path = path or SCALER_PATH
        with open(path, "rb") as f:
            self.scaler = pickle.load(f)
        self.is_fitted = True
        print(f"Scaler loaded from {path}")


def create_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic sample data for testing.
    
    Creates realistic-looking user behavior data with controlled randomness.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with synthetic user data
    """
    np.random.seed(42)
    
    data = {
        "user_id": range(1, n_samples + 1),
        "monthly_budget": np.random.uniform(100, 1000, n_samples),
        "total_clothing_spent_last_month": np.random.uniform(20, 800, n_samples),
        "number_of_purchases_last_month": np.random.randint(0, 15, n_samples),
        "wardrobe_size": np.random.randint(20, 200, n_samples),
        "total_times_worn": np.random.randint(10, 500, n_samples),
        "average_decision_time_minutes": np.random.uniform(1, 30, n_samples),
        "shopping_frequency_per_month": np.random.uniform(0.5, 8, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Generate target variable with realistic correlation to features
    # Next month spending is influenced by: past spending, budget, shopping frequency
    df["next_month_spending"] = (
        0.4 * df["total_clothing_spent_last_month"] +
        0.2 * df["monthly_budget"] +
        15 * df["shopping_frequency_per_month"] +
        5 * df["number_of_purchases_last_month"] +
        np.random.normal(0, 50, n_samples)  # Add noise
    ).clip(0, None)  # Ensure non-negative
    
    # Introduce some missing values (5% random)
    for col in ["total_clothing_spent_last_month", "average_decision_time_minutes"]:
        mask = np.random.random(n_samples) < 0.05
        df.loc[mask, col] = np.nan
    
    print(f"Generated {n_samples} synthetic samples")
    return df
