"""
Comprehensive System Test Suite
Tests all components before proceeding to model implementation
"""

import sys
from pathlib import Path
import traceback
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_test(name, passed, message=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} - {name}")
    if message:
        print(f"    {Colors.CYAN}{message}{Colors.RESET}")


def print_warning(message):
    print(f"{Colors.YELLOW}⚠ WARNING: {message}{Colors.RESET}")


def print_info(message):
    print(f"{Colors.CYAN}ℹ INFO: {message}{Colors.RESET}")


class SystemTester:
    """Comprehensive system testing"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
    
    def test_1_environment(self):
        """Test 1: Environment and Dependencies"""
        print_header("TEST 1: Environment & Dependencies")
        
        tests_passed = 0
        tests_total = 0
        
        # Test Python version
        tests_total += 1
        try:
            import sys
            version = sys.version_info
            passed = version.major == 3 and version.minor >= 9
            print_test(
                "Python Version", 
                passed, 
                f"Python {version.major}.{version.minor}.{version.micro}"
            )
            if passed:
                tests_passed += 1
        except Exception as e:
            print_test("Python Version", False, str(e))
        
        # Test critical packages
        critical_packages = [
            'pandas', 'numpy', 'psycopg2', 'sqlalchemy', 
            'torch', 'torch_geometric', 'networkx'
        ]
        
        for package in critical_packages:
            tests_total += 1
            try:
                if package == 'torch_geometric':
                    __import__('torch_geometric')
                else:
                    __import__(package)
                print_test(f"Package: {package}", True)
                tests_passed += 1
            except ImportError:
                print_test(f"Package: {package}", False, "Not installed")
                self.errors.append(f"Missing package: {package}")
        
        self.results['environment'] = (tests_passed, tests_total)
        return tests_passed == tests_total
    
    def test_2_configuration(self):
        """Test 2: Configuration Module"""
        print_header("TEST 2: Configuration Module")
        
        tests_passed = 0
        tests_total = 0
        
        # Test config import
        tests_total += 1
        try:
            from src.config.config import config
            print_test("Import config module", True)
            tests_passed += 1
        except Exception as e:
            print_test("Import config module", False, str(e))
            self.errors.append(f"Config import failed: {e}")
            self.results['configuration'] = (tests_passed, tests_total)
            return False
        
        # Test critical config values
        config_checks = [
            ('DB_HOST', config.DB_HOST),
            ('DB_PORT', config.DB_PORT),
            ('DB_NAME', config.DB_NAME),
            ('DB_USER', config.DB_USER),
        ]
        
        for name, value in config_checks:
            tests_total += 1
            if value:
                print_test(f"Config: {name}", True, str(value))
                tests_passed += 1
            else:
                print_test(f"Config: {name}", False, "Not set")
        
        # Test directory creation
        tests_total += 1
        try:
            config.ensure_directories()
            print_test("Create directories", True)
            tests_passed += 1
        except Exception as e:
            print_test("Create directories", False, str(e))
        
        self.results['configuration'] = (tests_passed, tests_total)
        return tests_passed == tests_total
    
    def test_3_database_connection(self):
        """Test 3: Database Connection"""
        print_header("TEST 3: Database Connection")
        
        tests_passed = 0
        tests_total = 0
        
        # Test database import
        tests_total += 1
        try:
            from src.database.connection import db
            print_test("Import database module", True)
            tests_passed += 1
        except Exception as e:
            print_test("Import database module", False, str(e))
            self.errors.append(f"Database import failed: {e}")
            self.results['database'] = (tests_passed, tests_total)
            return False
        
        # Test connection
        tests_total += 1
        try:
            if db.test_connection():
                print_test("Database connection", True, "Connected successfully")
                tests_passed += 1
            else:
                print_test("Database connection", False, "Connection failed")
                self.errors.append("Cannot connect to database")
        except Exception as e:
            print_test("Database connection", False, str(e))
            self.errors.append(f"Database connection error: {e}")
        
        # Test table existence
        tables = ['account', 'merchant', 'device', 'transaction', 'shared_device']
        for table in tables:
            tests_total += 1
            try:
                count = db.get_table_count(table)
                print_test(f"Table exists: {table}", True, f"{count:,} rows")
                tests_passed += 1
            except Exception as e:
                print_test(f"Table exists: {table}", False, str(e))
                self.errors.append(f"Table {table} not accessible")
        
        self.results['database'] = (tests_passed, tests_total)
        return tests_passed == tests_total
    
    def test_4_data_loader(self):
        """Test 4: Data Loader Module"""
        print_header("TEST 4: Data Loader Module")
        
        tests_passed = 0
        tests_total = 0
        
        # Test import
        tests_total += 1
        try:
            from src.preprocessing.data_loader import DataLoader
            print_test("Import DataLoader", True)
            tests_passed += 1
        except Exception as e:
            print_test("Import DataLoader", False, str(e))
            self.errors.append(f"DataLoader import failed: {e}")
            self.results['data_loader'] = (tests_passed, tests_total)
            return False
        
        # Test instantiation
        tests_total += 1
        try:
            loader = DataLoader()
            print_test("Instantiate DataLoader", True)
            tests_passed += 1
        except Exception as e:
            print_test("Instantiate DataLoader", False, str(e))
            self.results['data_loader'] = (tests_passed, tests_total)
            return False
        
        # Test data file existence
        from src.config.config import config
        required_files = ['train_transaction.csv', 'train_identity.csv']
        
        for filename in required_files:
            tests_total += 1
            filepath = config.DATA_RAW_PATH / filename
            if filepath.exists():
                size_mb = filepath.stat().st_size / (1024 * 1024)
                print_test(f"Dataset file: {filename}", True, f"{size_mb:.1f} MB")
                tests_passed += 1
            else:
                print_test(f"Dataset file: {filename}", False, "Not found")
                print_warning(f"Download dataset to {config.DATA_RAW_PATH}")
        
        self.results['data_loader'] = (tests_passed, tests_total)
        return tests_passed >= tests_total - len(required_files)  # Allow missing dataset files
    
    def test_5_database_inserter(self):
        """Test 5: Database Inserter Module"""
        print_header("TEST 5: Database Inserter Module")
        
        tests_passed = 0
        tests_total = 0
        
        # Test import
        tests_total += 1
        try:
            from src.preprocessing.db_inserter import DatabaseInserter
            print_test("Import DatabaseInserter", True)
            tests_passed += 1
        except Exception as e:
            print_test("Import DatabaseInserter", False, str(e))
            self.errors.append(f"DatabaseInserter import failed: {e}")
            self.results['db_inserter'] = (tests_passed, tests_total)
            return False
        
        # Test instantiation
        tests_total += 1
        try:
            inserter = DatabaseInserter(batch_size=1000)
            print_test("Instantiate DatabaseInserter", True)
            tests_passed += 1
        except Exception as e:
            print_test("Instantiate DatabaseInserter", False, str(e))
        
        self.results['db_inserter'] = (tests_passed, tests_total)
        return tests_passed == tests_total
    
    def test_6_graph_builder(self):
        """Test 6: Graph Builder Module"""
        print_header("TEST 6: Graph Builder Module")
        
        tests_passed = 0
        tests_total = 0
        
        # Test import
        tests_total += 1
        try:
            from src.graph.build_graph import GraphBuilder
            print_test("Import GraphBuilder", True)
            tests_passed += 1
        except Exception as e:
            print_test("Import GraphBuilder", False, str(e))
            self.errors.append(f"GraphBuilder import failed: {e}")
            self.results['graph_builder'] = (tests_passed, tests_total)
            return False
        
        # Test instantiation
        tests_total += 1
        try:
            builder = GraphBuilder()
            print_test("Instantiate GraphBuilder", True)
            tests_passed += 1
        except Exception as e:
            print_test("Instantiate GraphBuilder", False, str(e))
        
        # Test PyTorch Geometric
        tests_total += 1
        try:
            from torch_geometric.data import HeteroData
            data = HeteroData()
            print_test("PyTorch Geometric HeteroData", True)
            tests_passed += 1
        except Exception as e:
            print_test("PyTorch Geometric HeteroData", False, str(e))
        
        self.results['graph_builder'] = (tests_passed, tests_total)
        return tests_passed == tests_total
    
    def test_7_data_verification(self):
        """Test 7: Data Verification Module"""
        print_header("TEST 7: Data Verification Module")
        
        tests_passed = 0
        tests_total = 0
        
        # Test import
        tests_total += 1
        try:
            from src.preprocessing.verify_data import DataVerifier
            print_test("Import DataVerifier", True)
            tests_passed += 1
        except Exception as e:
            print_test("Import DataVerifier", False, str(e))
            self.errors.append(f"DataVerifier import failed: {e}")
            self.results['data_verification'] = (tests_passed, tests_total)
            return False
        
        # Test instantiation
        tests_total += 1
        try:
            verifier = DataVerifier()
            print_test("Instantiate DataVerifier", True)
            tests_passed += 1
        except Exception as e:
            print_test("Instantiate DataVerifier", False, str(e))
        
        self.results['data_verification'] = (tests_passed, tests_total)
        return tests_passed == tests_total
    
    def test_8_file_structure(self):
        """Test 8: Project File Structure"""
        print_header("TEST 8: Project File Structure")
        
        tests_passed = 0
        tests_total = 0
        
        critical_files = [
            'README.md',
            'QUICKSTART.md',
            'requirements.txt',
            '.env.example',
            'verify_setup.py',
            'src/config/config.py',
            'src/database/connection.py',
            'src/database/setup_db.py',
            'src/preprocessing/data_loader.py',
            'src/preprocessing/db_inserter.py',
            'src/preprocessing/load_data.py',
            'src/preprocessing/verify_data.py',
            'src/graph/build_graph.py',
            'database/schema/create_tables.sql',
            'database/queries/analytical_queries.sql',
            'docs/ER_diagram.md',
            'docs/graph_schema.md',
            'docs/data_loading_guide.md',
        ]
        
        base_path = Path(__file__).parent
        
        for filepath in critical_files:
            tests_total += 1
            full_path = base_path / filepath
            if full_path.exists():
                print_test(f"File: {filepath}", True)
                tests_passed += 1
            else:
                print_test(f"File: {filepath}", False, "Missing")
        
        self.results['file_structure'] = (tests_passed, tests_total)
        return tests_passed == tests_total
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print_header("TEST SUMMARY REPORT")
        
        total_passed = 0
        total_tests = 0
        
        print(f"\n{Colors.BOLD}Test Results by Category:{Colors.RESET}\n")
        
        for category, (passed, total) in self.results.items():
            total_passed += passed
            total_tests += total
            percentage = (passed / total * 100) if total > 0 else 0
            
            status_color = Colors.GREEN if passed == total else Colors.YELLOW if passed > 0 else Colors.RED
            
            print(f"{status_color}{category.upper().replace('_', ' ')}: {passed}/{total} ({percentage:.1f}%){Colors.RESET}")
        
        print(f"\n{Colors.BOLD}Overall Results:{Colors.RESET}")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {Colors.GREEN}{total_passed}{Colors.RESET}")
        print(f"  Failed: {Colors.RED}{total_tests - total_passed}{Colors.RESET}")
        
        if total_passed == total_tests:
            print(f"\n{Colors.BOLD}{Colors.GREEN}✓ ALL TESTS PASSED!{Colors.RESET}")
            print(f"{Colors.GREEN}System is ready for model implementation.{Colors.RESET}")
            return True
        else:
            percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
            print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠ TESTS PARTIALLY PASSED ({percentage:.1f}%){Colors.RESET}")
            
            if self.errors:
                print(f"\n{Colors.BOLD}Critical Issues:{Colors.RESET}")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {Colors.RED}{error}{Colors.RESET}")
            
            return False
    
    def run_all_tests(self):
        """Run all test suites"""
        start_time = datetime.now()
        
        print(f"{Colors.BOLD}{Colors.CYAN}")
        print("=" * 70)
        print("  FRAUD DETECTION SYSTEM - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"{Colors.RESET}")
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run all tests
        test_methods = [
            self.test_1_environment,
            self.test_2_configuration,
            self.test_3_database_connection,
            self.test_4_data_loader,
            self.test_5_database_inserter,
            self.test_6_graph_builder,
            self.test_7_data_verification,
            self.test_8_file_structure,
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print_test(test_method.__name__, False, f"Unexpected error: {e}")
                traceback.print_exc()
        
        # Generate report
        all_passed = self.generate_report()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{Colors.CYAN}End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.CYAN}Duration: {duration:.2f} seconds{Colors.RESET}")
        print(f"\n{'=' * 70}\n")
        
        return all_passed


def main():
    """Main test execution"""
    tester = SystemTester()
    all_passed = tester.run_all_tests()
    
    if all_passed:
        print(f"{Colors.GREEN}✓ Ready to proceed with model implementation!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠ Please fix the issues above before proceeding.{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
