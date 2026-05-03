"""
SYSTEM VALIDATION SCRIPT
Tests all components before running the main application
"""

import sys
import os
import traceback
from datetime import datetime


class SystemValidator:
    """Validates system components and dependencies."""
    
    def __init__(self):
        """Initialize validator."""
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.test_count = 0
    
    def print_header(self, title):
        """Print section header."""
        print(f"\n{'='*70}")
        print(f"{title}")
        print(f"{'='*70}\n")
    
    def print_test(self, name, status, details=""):
        """Print test result."""
        status_symbol = "✓" if status else "✗"
        print(f"{status_symbol} {name}")
        if details:
            print(f"  → {details}")
    
    def print_summary(self):
        """Print test summary."""
        self.print_header("TEST SUMMARY")
        
        print(f"Passed:  {len(self.results['passed'])}")
        print(f"Failed:  {len(self.results['failed'])}")
        print(f"Warnings: {len(self.results['warnings'])}")
        
        if self.results['failed']:
            print(f"\n❌ FAILED TESTS:")
            for fail in self.results['failed']:
                print(f"  • {fail}")
        
        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS:")
            for warn in self.results['warnings']:
                print(f"  • {warn}")
        
        if not self.results['failed']:
            print(f"\n✓ All tests passed! System is ready.")
            return True
        else:
            print(f"\n❌ Some tests failed. Please fix issues before running the system.")
            return False
    
    # ========================================================================
    # PYTHON VERSION TEST
    # ========================================================================
    
    def test_python_version(self):
        """Test Python version."""
        self.print_header("1. PYTHON ENVIRONMENT")
        
        version_info = sys.version_info
        version_string = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        
        if version_info >= (3, 8):
            self.results['passed'].append(f"Python {version_string}")
            self.print_test("Python Version", True, f"Version {version_string}")
        else:
            self.results['failed'].append(f"Python version {version_string} < 3.8")
            self.print_test("Python Version", False, f"Version {version_string} (need 3.8+)")
    
    # ========================================================================
    # PACKAGE TESTS
    # ========================================================================
    
    def test_packages(self):
        """Test package imports."""
        self.print_header("2. REQUIRED PACKAGES")
        
        packages = {
            'numpy': 'Numerical computing',
            'pandas': 'Data manipulation',
            'sklearn': 'Machine learning',
            'statsmodels': 'Statistical models',
            'matplotlib': 'Visualization'
        }
        
        for package, description in packages.items():
            try:
                __import__(package)
                
                # Get version
                if package == 'sklearn':
                    import sklearn
                    version = sklearn.__version__
                elif package == 'statsmodels':
                    import statsmodels
                    version = statsmodels.__version__
                else:
                    mod = __import__(package)
                    version = getattr(mod, '__version__', 'unknown')
                
                self.results['passed'].append(f"{package} ({version})")
                self.print_test(f"{package}", True, f"Version {version}")
            
            except ImportError:
                self.results['failed'].append(f"{package} not found")
                self.print_test(f"{package}", False, "Not installed")

        try:
            import tensorflow
            self.results['passed'].append(f"tensorflow ({tensorflow.__version__})")
            self.print_test("tensorflow", True, f"Version {tensorflow.__version__}")
        except ImportError:
            self.results['warnings'].append("tensorflow not installed; using scikit-learn neural fallback")
            self.print_test("tensorflow", True, "Optional; scikit-learn fallback will be used")
    
    # ========================================================================
    # PROJECT FILES TEST
    # ========================================================================
    
    def test_project_files(self):
        """Test project file structure."""
        self.print_header("3. PROJECT FILES")
        
        required_files = [
            'config.py',
            'data_generator.py',
            'data_processor.py',
            'models.py',
            'ensemble.py',
            'alert_system.py',
            'visualizer.py',
            'main.py',
            'requirements.txt',
            'README.md',
            'quickstart.py'
        ]
        
        for filename in required_files:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                self.results['passed'].append(f"{filename} ({size} bytes)")
                self.print_test(f"{filename}", True)
            else:
                self.results['failed'].append(f"{filename} missing")
                self.print_test(f"{filename}", False, "NOT FOUND")
    
    # ========================================================================
    # DIRECTORY TESTS
    # ========================================================================
    
    def test_directories(self):
        """Test output directories."""
        self.print_header("4. OUTPUT DIRECTORIES")
        
        directories = {
            'outputs': 'Main output directory',
            'outputs/data': 'CSV data export',
            'outputs/graphs': 'PNG visualizations',
            'outputs/logs': 'Log files'
        }
        
        for dirname, description in directories.items():
            if os.path.exists(dirname):
                self.results['passed'].append(f"{dirname}")
                self.print_test(f"{dirname}", True, description)
            else:
                try:
                    os.makedirs(dirname, exist_ok=True)
                    self.results['passed'].append(f"{dirname} (created)")
                    self.print_test(f"{dirname}", True, "Created successfully")
                except Exception as e:
                    self.results['failed'].append(f"Cannot create {dirname}")
                    self.print_test(f"{dirname}", False, f"Cannot create: {e}")
    
    # ========================================================================
    # CONFIGURATION TEST
    # ========================================================================
    
    def test_configuration(self):
        """Test configuration file."""
        self.print_header("5. CONFIGURATION")
        
        try:
            from config import (
                PROJECT_NAME, BASELINE_VALUES, SAFE_RANGES,
                MODEL_WEIGHTS, SAFE_RANGES
            )
            
            self.print_test("Config import", True)
            
            # Validate baseline values
            expected_params = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
            if all(p in BASELINE_VALUES for p in expected_params):
                self.results['passed'].append("All baseline values present")
                self.print_test("Baseline values", True, f"{len(BASELINE_VALUES)} parameters")
            else:
                self.results['failed'].append("Missing baseline values")
                self.print_test("Baseline values", False, "Incomplete")
            
            # Validate safe ranges
            if all(p in SAFE_RANGES for p in expected_params):
                self.results['passed'].append("All safe ranges present")
                self.print_test("Safe ranges", True, f"{len(SAFE_RANGES)} parameters")
            else:
                self.results['failed'].append("Missing safe ranges")
                self.print_test("Safe ranges", False, "Incomplete")
            
            # Validate model weights
            weights_sum = sum(MODEL_WEIGHTS.values())
            if abs(weights_sum - 1.0) < 0.01:
                self.results['passed'].append("Model weights valid")
                self.print_test("Model weights", True, f"Sum = {weights_sum:.2f}")
            else:
                self.results['warnings'].append(f"Model weights sum = {weights_sum:.2f}")
                self.print_test("Model weights", True, f"Sum = {weights_sum:.2f} (non-standard)")
        
        except Exception as e:
            self.results['failed'].append(f"Config error: {e}")
            self.print_test("Configuration", False, str(e))
    
    # ========================================================================
    # MODULE TESTS
    # ========================================================================
    
    def test_modules(self):
        """Test module imports."""
        self.print_header("6. SYSTEM MODULES")
        
        modules = {
            'data_generator': 'WaterQualityDataGenerator',
            'data_processor': 'DataProcessor',
            'models': 'RandomForestModel',
            'ensemble': 'EnsemblePredictor',
            'alert_system': 'AlertSystem',
            'visualizer': 'WaterQualityVisualizer'
        }
        
        for module_name, class_name in modules.items():
            try:
                module = __import__(module_name)
                if hasattr(module, class_name):
                    self.results['passed'].append(f"{module_name}.{class_name}")
                    self.print_test(f"{module_name}", True)
                else:
                    self.results['failed'].append(f"{class_name} not found in {module_name}")
                    self.print_test(f"{module_name}", False, f"{class_name} not found")
            except Exception as e:
                self.results['failed'].append(f"Cannot import {module_name}: {e}")
                self.print_test(f"{module_name}", False, str(e))
    
    # ========================================================================
    # DATA GENERATOR TEST
    # ========================================================================
    
    def test_data_generator(self):
        """Test data generator functionality."""
        self.print_header("7. DATA GENERATION")
        
        try:
            from data_generator import WaterQualityDataGenerator
            
            generator = WaterQualityDataGenerator(seed=42)
            
            # Generate single record
            record = generator.generate_single_record()
            if 'Salinity' in record and 'Timestamp' in record:
                self.results['passed'].append("Single record generation")
                self.print_test("Generate single record", True)
            else:
                self.results['failed'].append("Record missing fields")
                self.print_test("Generate single record", False, "Incomplete record")
            
            # Generate batch
            batch = generator.generate_batch(10)
            if len(batch) == 10:
                self.results['passed'].append("Batch generation (10 records)")
                self.print_test("Generate batch (10)", True)
            else:
                self.results['failed'].append(f"Batch size incorrect: {len(batch)}")
                self.print_test("Generate batch (10)", False, f"Got {len(batch)}")
        
        except Exception as e:
            self.results['failed'].append(f"Data generator error: {e}")
            self.print_test("Data generation", False, str(e))
            traceback.print_exc()
    
    # ========================================================================
    # DATA PROCESSOR TEST
    # ========================================================================
    
    def test_data_processor(self):
        """Test data processor functionality."""
        self.print_header("8. DATA PROCESSING")
        
        try:
            from data_generator import WaterQualityDataGenerator
            from data_processor import DataProcessor
            
            generator = WaterQualityDataGenerator(seed=42)
            data = generator.generate_batch(50)
            
            processor = DataProcessor()
            
            # Test preparation
            prepared = processor.prepare_data(data.copy(), fit=True)
            
            if len(prepared) > 0:
                self.results['passed'].append("Data preparation")
                self.print_test("Prepare data", True, f"Shape: {prepared.shape}")
            else:
                self.results['failed'].append("Preparation resulted in empty data")
                self.print_test("Prepare data", False, "Empty result")
            
            # Test normalization
            scaled = processor.normalize_features(data.copy(), fit=True)
            if len(scaled) == len(data):
                self.results['passed'].append("Feature normalization")
                self.print_test("Normalize features", True)
            else:
                self.results['failed'].append("Normalization size mismatch")
                self.print_test("Normalize features", False)
        
        except Exception as e:
            self.results['failed'].append(f"Data processor error: {e}")
            self.print_test("Data processing", False, str(e))
            traceback.print_exc()
    
    # ========================================================================
    # SYSTEM MEMORY TEST
    # ========================================================================
    
    def test_system_memory(self):
        """Test available system memory."""
        self.print_header("9. SYSTEM RESOURCES")
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb > 1:
                self.results['passed'].append(f"Sufficient memory ({available_gb:.1f}GB available)")
                self.print_test("Available memory", True, f"{available_gb:.1f}GB")
            else:
                self.results['warnings'].append(f"Low memory ({available_gb:.1f}GB)")
                self.print_test("Available memory", True, f"{available_gb:.1f}GB (low)")
        
        except ImportError:
            self.results['warnings'].append("psutil not installed (optional)")
            self.print_test("Memory check", True, "psutil not available (optional)")
        except Exception as e:
            self.results['warnings'].append(f"Memory check failed: {e}")
    
    # ========================================================================
    # MAIN TEST RUNNER
    # ========================================================================
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*68 + "║")
        print("║" + "SYSTEM VALIDATION & DIAGNOSTICS".center(68) + "║")
        print("║" + "Smart Prawn Hatchery System".center(68) + "║")
        print("║" + " "*68 + "║")
        print("╚" + "="*68 + "╝")
        
        print(f"\nTest started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        self.test_python_version()
        self.test_packages()
        self.test_project_files()
        self.test_directories()
        self.test_configuration()
        self.test_modules()
        self.test_data_generator()
        self.test_data_processor()
        self.test_system_memory()
        
        # Print summary
        success = self.print_summary()
        
        print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return success


def main():
    """Main entry point."""
    validator = SystemValidator()
    success = validator.run_all_tests()
    
    if success:
        print("\n✓ SYSTEM VALIDATION COMPLETE - READY TO RUN")
        print("\nNext steps:")
        print("  1. python quickstart.py    (Interactive menu)")
        print("  2. python main.py          (Direct execution)")
        print("  3. python advanced_usage.py (Example code)\n")
        return 0
    else:
        print("\n❌ VALIDATION FAILED - PLEASE FIX ISSUES ABOVE\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
