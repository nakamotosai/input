import os

target = 'c:/Users/sai/jp/ui_manager.py'
extension = 'c:/Users/sai/jp/ui_extension.py'

with open(target, 'rb') as f:
    data = f.read()

idx = data.find(b'\x00')

if idx != -1:
    print(f"Found null byte at {idx}. Truncating...")
    clean_data = data[:idx]
    
    # Remove potentially partial line at the end
    last_nl = clean_data.rfind(b'\n')
    if last_nl != -1:
        clean_data = clean_data[:last_nl+1]
        
    with open(target, 'wb') as f:
        f.write(clean_data)
        
        # Read extension and append
        with open(extension, 'rb') as ext:
            f.write(ext.read())
            
    print("Successfully repaired ui_manager.py")
else:
    print("No null bytes found. File might be clean.")
