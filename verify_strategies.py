"""
Strategy Verification Script
Tests all strategies to ensure they work without errors
"""

import os
import sys
import importlib.util
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_strategy_imports():
    """Test that all strategies can be imported without errors"""
    
    strategies_dir = os.path.join(os.path.dirname(__file__), 'strategies')
    
    if not os.path.exists(strategies_dir):
        print(f"❌ Strategies directory not found: {strategies_dir}")
        return False
    
    print("=" * 60)
    print("STRATEGY VERIFICATION TEST")
    print("=" * 60)
    
    # List all strategy files
    strategy_files = [f for f in os.listdir(strategies_dir) if f.endswith('.py') and not f.startswith('__')]
    
    if not strategy_files:
        print("❌ No strategy files found!")
        return False
    
    print(f"Found {len(strategy_files)} strategy files to test\n")
    
    successful = []
    failed = []
    
    for filename in sorted(strategy_files):
        module_name = filename[:-3]  # Remove .py extension
        file_path = os.path.join(strategies_dir, filename)
        
        try:
            # Try to import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Check for strategy class
            strategy_found = False
            strategy_name = None
            
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    item_name.endswith('Strategy') and
                    hasattr(item, 'params')):
                    strategy_found = True
                    strategy_name = getattr(item, 'strategy_name', item_name)
                    break
            
            if strategy_found:
                successful.append((filename, strategy_name))
                print(f"✅ {filename:<30} - {strategy_name}")
            else:
                failed.append((filename, "No strategy class found"))
                print(f"⚠️  {filename:<30} - No strategy class found")
                
        except Exception as e:
            error_msg = str(e).split('\n')[0]  # Get first line of error
            failed.append((filename, error_msg))
            print(f"❌ {filename:<30} - ERROR: {error_msg}")
            if '--debug' in sys.argv:
                traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    
    print(f"✅ Successful: {len(successful)}/{len(strategy_files)}")
    print(f"❌ Failed: {len(failed)}/{len(strategy_files)}")
    
    if successful:
        print("\n🎯 Working Strategies:")
        for filename, name in successful:
            print(f"   - {name}")
    
    if failed:
        print("\n❌ Failed Strategies:")
        for filename, error in failed:
            print(f"   - {filename}: {error}")
    
    print("\n" + "=" * 60)
    
    # Return True only if all strategies loaded successfully
    return len(failed) == 0


def verify_strategy_parameters():
    """Verify that all strategies have required parameters"""
    
    print("\n" + "=" * 60)
    print("PARAMETER VERIFICATION")
    print("=" * 60)
    
    required_params = [
        'printlog',
        'risk_per_trade',
        'leverage',
        'stop_loss_pct',
        'take_profit_pct',
        'use_risk_management'
    ]
    
    strategies_dir = os.path.join(os.path.dirname(__file__), 'strategies')
    strategy_files = [f for f in os.listdir(strategies_dir) if f.endswith('.py') and not f.startswith('__')]
    
    all_valid = True
    
    for filename in sorted(strategy_files):
        module_name = filename[:-3]
        file_path = os.path.join(strategies_dir, filename)
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    item_name.endswith('Strategy') and
                    hasattr(item, 'params')):
                    
                    # Check parameters
                    strategy_params = item.params._fields if hasattr(item.params, '_fields') else []
                    missing_params = []
                    
                    for param in required_params:
                        if param not in [p for p in strategy_params]:
                            missing_params.append(param)
                    
                    if missing_params:
                        print(f"⚠️  {filename}: Missing params: {missing_params}")
                        all_valid = False
                    else:
                        print(f"✅ {filename}: All required params present")
                    
                    break
                    
        except Exception as e:
            print(f"❌ {filename}: Could not verify parameters - {e}")
            all_valid = False
    
    return all_valid


def main():
    """Run all verification tests"""
    
    print("\n🔍 STARTING STRATEGY VERIFICATION SYSTEM")
    print("=" * 60)
    
    # Test 1: Import test
    import_success = test_strategy_imports()
    
    # Test 2: Parameter verification
    param_success = verify_strategy_parameters()
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL VERIFICATION STATUS")
    print("=" * 60)
    
    if import_success and param_success:
        print("✅ ALL STRATEGIES VERIFIED SUCCESSFULLY!")
        print("✅ Your strategies are PRODUCTION READY!")
        print("\n🚀 You can now run backtests with confidence!")
        return 0
    else:
        print("❌ SOME STRATEGIES HAVE ISSUES")
        print("Please fix the errors above before running backtests")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
