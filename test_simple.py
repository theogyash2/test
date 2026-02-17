print("Script started!")

try:
    print("Importing modules...")
    import json
    import os
    import subprocess
    print("✅ Imports successful")
    
    print("Checking config file...")
    config_path = "C:/production/config/unicorn_config.json"
    if os.path.exists(config_path):
        print(f"✅ Config exists: {config_path}")
        with open(config_path) as f:
            config = json.load(f)
            print(f"✅ Workers defined: {len(config['workers'])}")
    else:
        print(f"❌ Config not found: {config_path}")
    
    print("Test complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

input("Press Enter to exit...")