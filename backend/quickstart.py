"""
Quick Start Guide - Smart Prawn Hatchery System
Run this script to test the system with predefined configurations.
"""

import os
import sys

def check_environment():
    """Check if Python environment is properly set up."""
    print("=" * 70)
    print("SYSTEM ENVIRONMENT CHECK")
    print("=" * 70)
    
    # Check Python version
    print(f"\nPython Version: {sys.version}")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required!")
        return False
    
    print("✓ Python version OK")
    
    # Check required packages
    required_packages = [
        'numpy',
        'pandas',
        'sklearn',
        'statsmodels',
        'matplotlib'
    ]
    
    print("\nChecking required packages:")
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"\nInstall them with:")
        print(f"pip install -r requirements.txt")
        return False

    try:
        __import__('tensorflow')
        print("✓ tensorflow")
    except ImportError:
        print("⚠ tensorflow - optional; scikit-learn neural fallback will be used")
    
    print("\n✓ All required packages installed")
    return True


def show_menu():
    """Display main menu."""
    print("\n" + "=" * 70)
    print("SMART PRAWN HATCHERY - QUICK START MENU")
    print("=" * 70)
    print("\n1. Run Full Simulation (12 iterations)")
    print("2. Run Extended Simulation (24 iterations)")
    print("3. Show Configuration")
    print("4. Check System Status")
    print("5. Exit")
    print("\n" + "=" * 70)


def run_simulation(num_iterations=12):
    """Run the main simulation."""
    print(f"\nStarting simulation with {num_iterations} iterations...")
    print("(This may take a few minutes depending on your system)\n")
    
    try:
        from main import SmartHatcherySystem
        
        system = SmartHatcherySystem()
        system.initialize_system()
        system.run_continuous_loop(num_iterations=num_iterations, save_data=True)
        
        print("\n✓ Simulation completed successfully!")
        return True
    
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_configuration():
    """Display current configuration."""
    print("\n" + "=" * 70)
    print("SYSTEM CONFIGURATION")
    print("=" * 70)
    
    from config import (
        BASELINE_VALUES, SAFE_RANGES, MODEL_WEIGHTS,
        ANOMALY_PROBABILITY, SIMULATION_HOUR_INTERVAL,
        PREDICTION_HORIZON
    )
    
    print("\n[BASELINE VALUES]")
    for param, value in BASELINE_VALUES.items():
        print(f"  {param}: {value}")
    
    print("\n[SAFE RANGES]")
    for param, range_vals in SAFE_RANGES.items():
        print(f"  {param}: {range_vals['min']:.1f} - {range_vals['max']:.1f}")
    
    print("\n[MODEL WEIGHTS]")
    for model, weight in MODEL_WEIGHTS.items():
        print(f"  {model}: {weight * 100:.0f}%")
    
    print(f"\n[SIMULATION PARAMETERS]")
    print(f"  Anomaly Probability: {ANOMALY_PROBABILITY * 100:.1f}%")
    print(f"  Hour Interval: {SIMULATION_HOUR_INTERVAL} second(s)")
    print(f"  Prediction Horizon: {PREDICTION_HORIZON} hours")
    
    print("\n" + "=" * 70)


def show_status():
    """Show system status and files."""
    print("\n" + "=" * 70)
    print("SYSTEM STATUS")
    print("=" * 70)
    
    from config import DATA_DIR, GRAPHS_DIR
    
    print(f"\nProject Directory: {os.getcwd()}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Graphs Directory: {GRAPHS_DIR}")
    
    print(f"\n[OUTPUT FILES]")
    
    # Count data files
    if os.path.exists(DATA_DIR):
        data_files = os.listdir(DATA_DIR)
        print(f"  CSV files: {len([f for f in data_files if f.endswith('.csv')])}")
    else:
        print(f"  CSV files: 0")
    
    # Count graph files
    if os.path.exists(GRAPHS_DIR):
        graph_files = os.listdir(GRAPHS_DIR)
        print(f"  PNG files: {len([f for f in graph_files if f.endswith('.png')])}")
    else:
        print(f"  PNG files: 0")
    
    print("\n✓ System ready for operation")
    print("=" * 70)


def main():
    """Main menu loop."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "AI-Based Smart Prawn Hatchery System".center(68) + "║")
    print("║" + "Water Quality Prediction and Monitoring".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment check failed. Please install missing dependencies.")
        sys.exit(1)
    
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == '1':
                if run_simulation(num_iterations=12):
                    print("\nSimulation completed! Check outputs/ directory for results.")
            
            elif choice == '2':
                if run_simulation(num_iterations=24):
                    print("\nSimulation completed! Check outputs/ directory for results.")
            
            elif choice == '3':
                show_configuration()
            
            elif choice == '4':
                show_status()
            
            elif choice == '5':
                print("\nGoodbye! 👋")
                break
            
            else:
                print("\n❌ Invalid choice. Please enter 1-5.")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
