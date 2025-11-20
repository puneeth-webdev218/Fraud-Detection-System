"""
System Verification Script
Tests all components of the fraud detection system
"""

import sys
from pathlib import Path
import importlib.util

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_status(test_name, passed, message=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} - {test_name}")
    if message:
        print(f"        {message}")


def test_python_version():
    """Test Python version"""
    import sys
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 9
    print_status(
        "Python Version", 
        passed, 
        f"Python {version.major}.{version.minor}.{version.micro}"
    )
    return passed


def test_required_packages():
    """Test if required packages are installed"""
    packages = [
        'pandas',
        'numpy',
        'psycopg2',
        'sqlalchemy',
        'torch',
        'torch_geometric',
        'networkx',
        'streamlit',
        'plotly',
        'sklearn',
    ]
    
    all_passed = True
    for package in packages:
        try:
            if package == 'torch_geometric':
                importlib.import_module('torch_geometric')
            else:
                importlib.import_module(package)
            print_status(f"Package: {package}", True)
        except ImportError:
            print_status(f"Package: {package}", False, "Not installed")
            all_passed = False
    
    return all_passed


def test_project_structure():
    """Test if project directories exist"""
    base_dir = Path(__file__).parent
    directories = [
        'data/raw',
        'data/processed',
        'database/schema',
        'src/config',
        'src/database',
        'src/preprocessing',
        'src/graph',
        'src/models',
        'src/training',
        'src/visualization',
        'checkpoints',
        'logs',
    ]
    
    all_passed = True
    for directory in directories:
        dir_path = base_dir / directory
        exists = dir_path.exists()
        print_status(f"Directory: {directory}", exists)
        if not exists:
            all_passed = False
    
    return all_passed


def test_configuration():
    """Test configuration loading"""
    try:
        from src.config.config import config
        print_status("Configuration module", True, f"Database: {config.DB_NAME}")
        return True
    except Exception as e:
        print_status("Configuration module", False, str(e))
        return False


def test_database_connection():
    """Test database connectivity"""
    try:
        from src.database.connection import db
        
        # Test connection
        connected = db.test_connection()
        if not connected:
            print_status("Database connection", False, "Cannot connect to database")
            return False
        
        print_status("Database connection", True, f"Connected to {db.db_uri.split('@')[1]}")
        
        # Test table existence
        tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
        for table in tables:
            try:
                count = db.get_table_count(table)
                print_status(f"  Table: {table}", True, f"{count} rows")
            except Exception as e:
                print_status(f"  Table: {table}", False, str(e))
        
        return True
        
    except Exception as e:
        print_status("Database connection", False, str(e))
        return False


def test_environment_file():
    """Test if .env file exists and is configured"""
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print_status(".env file", False, "File not found. Copy from .env.example")
        return False
    
    # Check if critical variables are set
    from src.config.config import config
    
    issues = []
    if not config.DB_PASSWORD:
        issues.append("DB_PASSWORD not set")
    if not config.DB_NAME:
        issues.append("DB_NAME not set")
    
    if issues:
        print_status(".env file", False, ", ".join(issues))
        return False
    
    print_status(".env file", True, "Configured")
    return True


def test_dataset_files():
    """Check if dataset files are present"""
    from src.config.config import config
    
    files = [
        'train_transaction.csv',
        'train_identity.csv',
    ]
    
    all_present = True
    for file in files:
        file_path = config.DATA_RAW_PATH / file
        exists = file_path.exists()
        if exists:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print_status(f"Dataset: {file}", True, f"{size_mb:.1f} MB")
        else:
            print_status(f"Dataset: {file}", False, "Not found")
            all_present = False
    
    return all_present


def main():
    """Run all tests"""
    print_header("Fraud Detection System - Verification")
    
    results = {}
    
    # Test 1: Python Version
    print(f"\n{Colors.YELLOW}[Test 1/7] Python Version{Colors.RESET}")
    results['python'] = test_python_version()
    
    # Test 2: Required Packages
    print(f"\n{Colors.YELLOW}[Test 2/7] Required Packages{Colors.RESET}")
    results['packages'] = test_required_packages()
    
    # Test 3: Project Structure
    print(f"\n{Colors.YELLOW}[Test 3/7] Project Structure{Colors.RESET}")
    results['structure'] = test_project_structure()
    
    # Test 4: Environment File
    print(f"\n{Colors.YELLOW}[Test 4/7] Environment Configuration{Colors.RESET}")
    results['env'] = test_environment_file()
    
    # Test 5: Configuration
    print(f"\n{Colors.YELLOW}[Test 5/7] Configuration Module{Colors.RESET}")
    results['config'] = test_configuration()
    
    # Test 6: Database
    print(f"\n{Colors.YELLOW}[Test 6/7] Database Connection{Colors.RESET}")
    results['database'] = test_database_connection()
    
    # Test 7: Dataset
    print(f"\n{Colors.YELLOW}[Test 7/7] Dataset Files{Colors.RESET}")
    results['dataset'] = test_dataset_files()
    
    # Summary
    print_header("Verification Summary")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"Tests Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓{Colors.RESET}" if result else f"{Colors.RED}✗{Colors.RESET}"
        print(f"{status} {test_name.upper()}")
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All tests passed! System is ready.{Colors.RESET}\n")
        print("Next steps:")
        print("  1. python src/preprocessing/load_data.py")
        print("  2. python src/graph/build_graph.py")
        print("  3. python src/training/train.py")
        return 0
    else:
        print(f"{Colors.RED}✗ Some tests failed. Please fix the issues above.{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
