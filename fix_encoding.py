import os

target = 'c:/Users/sai/jp/ui_manager.py'
extension = 'c:/Users/sai/jp/ui_extension.py'

with open(target, 'rb') as f:
    data = f.read()

# Find first null byte which indicates UTF-16
idx = data.find(b'\x00')

if idx != -1:
    print(f"Found null byte at {idx}")
    # The garbage likely starts a bit before the null byte (e.g. BOM or the first char 'd' of 'def')
    # UTF-16 char 'd' is 'd\x00'.
    # If we cut at idx, we might keep 'd'.
    # We should cut at the point where the `>>` happened.
    # We know the original file was UTF-8. 
    # Let's inspect the bytes around idx.
    # It's safer to find the last valid newline of the UTF-8 part.
    
    pre_garbage = data[:idx]
    # Find the last \n in the pre_garbage
    last_newline = pre_garbage.rfind(b'\n')
    
    if last_newline != -1:
        clean_data = data[:last_newline+1]
        print(f"Truncating to {last_newline+1}")
        
        with open(target, 'wb') as f:
            f.write(clean_data)
            
        # Append extension
        with open(extension, 'rb') as ext:
            content = ext.read()
            f.write(content)
        print("Fixed ui_manager.py")
    else:
        print("Could not find safe truncation point")
else:
    print("No null bytes found, file might be clean or corrupted differently.")
