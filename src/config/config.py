"""
Configuration Management Module
Loads environment variables and provides configuration settings
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for the fraud detection system"""
    
    # Database Configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'fraud_detection')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    # Kaggle API Configuration
    KAGGLE_USERNAME: Optional[str] = os.getenv('KAGGLE_USERNAME')
    KAGGLE_KEY: Optional[str] = os.getenv('KAGGLE_KEY')
    
    # Model Training Configuration
    RANDOM_SEED: int = int(os.getenv('RANDOM_SEED', '42'))
    TRAIN_BATCH_SIZE: int = int(os.getenv('TRAIN_BATCH_SIZE', '128'))
    VAL_BATCH_SIZE: int = int(os.getenv('VAL_BATCH_SIZE', '256'))
    LEARNING_RATE: float = float(os.getenv('LEARNING_RATE', '0.001'))
    NUM_EPOCHS: int = int(os.getenv('NUM_EPOCHS', '100'))
    EARLY_STOPPING_PATIENCE: int = int(os.getenv('EARLY_STOPPING_PATIENCE', '10'))
    
    # Path Configuration
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_RAW_PATH: Path = BASE_DIR / os.getenv('DATA_RAW_PATH', 'data/raw')
    DATA_PROCESSED_PATH: Path = BASE_DIR / os.getenv('DATA_PROCESSED_PATH', 'data/processed')
    MODEL_CHECKPOINT_PATH: Path = BASE_DIR / os.getenv('MODEL_CHECKPOINT_PATH', 'checkpoints')
    LOG_PATH: Path = BASE_DIR / os.getenv('LOG_PATH', 'logs')
    
    # GNN Model Configuration
    GNN_MODEL_TYPE: str = os.getenv('GNN_MODEL_TYPE', 'GraphSAGE')
    HIDDEN_DIM: int = int(os.getenv('HIDDEN_DIM', '128'))
    NUM_LAYERS: int = int(os.getenv('NUM_LAYERS', '3'))
    DROPOUT: float = float(os.getenv('DROPOUT', '0.2'))
    
    # Dashboard Configuration
    DASHBOARD_HOST: str = os.getenv('DASHBOARD_HOST', 'localhost')
    DASHBOARD_PORT: int = int(os.getenv('DASHBOARD_PORT', '8501'))
    
    @classmethod
    def get_database_uri(cls) -> str:
        """Generate PostgreSQL database URI"""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist"""
        directories = [
            cls.DATA_RAW_PATH,
            cls.DATA_PROCESSED_PATH,
            cls.MODEL_CHECKPOINT_PATH,
            cls.LOG_PATH,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate critical configuration settings"""
        if not cls.DB_PASSWORD:
            print("Warning: DB_PASSWORD is not set!")
            return False
        
        if cls.KAGGLE_USERNAME is None or cls.KAGGLE_KEY is None:
            print("Warning: Kaggle API credentials not configured!")
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (excluding sensitive data)"""
        print("=" * 60)
        print("Configuration Settings")
        print("=" * 60)
        print(f"Database Host: {cls.DB_HOST}:{cls.DB_PORT}")
        print(f"Database Name: {cls.DB_NAME}")
        print(f"Database User: {cls.DB_USER}")
        print(f"Random Seed: {cls.RANDOM_SEED}")
        print(f"GNN Model: {cls.GNN_MODEL_TYPE}")
        print(f"Hidden Dim: {cls.HIDDEN_DIM}")
        print(f"Num Layers: {cls.NUM_LAYERS}")
        print(f"Learning Rate: {cls.LEARNING_RATE}")
        print(f"Batch Size: {cls.TRAIN_BATCH_SIZE}")
        print(f"Epochs: {cls.NUM_EPOCHS}")
        print("=" * 60)


# Create a singleton config instance
config = Config()

# Ensure directories exist
config.ensure_directories()


if __name__ == "__main__":
    # Test configuration
    config.print_config()
    print(f"\nConfiguration valid: {config.validate_config()}")
