import os
import sys

# Mock classes to simulate environment
class ModelInfo:
    def __init__(self, target_dir):
        self.target_dir = target_dir

MODELS = {
    "nllb_600m": ModelInfo(target_dir="nllb_600m_v1")
}

def is_model_installed(models_dir, model_id):
    print(f"Checking model: {model_id}")
    if model_id not in MODELS:
        print("Model ID not found in definitions")
        return False
    
    model = MODELS[model_id]
    target_path = os.path.join(models_dir, model.target_dir)
    print(f"Target path: {target_path}")
    
    if os.path.isdir(target_path):
        print("Directory exists.")
        files = os.listdir(target_path)
        print(f"Files in dir: {files}")
        
        # Check logic from original code
        has_file = any(f.endswith(('.onnx', '.bin', '.model', '.json')) for f in files)
        print(f"Direct file check result: {has_file}")
        
        if has_file:
            return True
            
        # Recursive check
        print("Checking recursively...")
        for root, dirs, files in os.walk(target_path):
            print(f"Scanning {root}: {files}")
            if any(f.endswith(('.onnx', '.bin', '.model')) for f in files):
                print("Found file recursively.")
                return True
    else:
        print("Directory does NOT exist.")
    
    return False

if __name__ == "__main__":
    # Simulate the path in the app
    current_dir = os.getcwd()
    models_dir = os.path.join(current_dir, "models")
    print(f"Simulated models dir: {models_dir}")
    
    result = is_model_installed(models_dir, "nllb_600m")
    print(f"Final Result: {result}")
