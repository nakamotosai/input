import os

target = 'c:/Users/sai/jp/ui_manager.py'
extension = 'c:/Users/sai/jp/ui_extension.py'

with open(target, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

clean_lines = []
found_garbage = False
for i, line in enumerate(lines):
    if '\ufffd' in line: # Replacement character
        print(f"Garbage found at line {i+1}: {line[:20]}...")
        found_garbage = True
        break
    # Also check for null bytes just in case text mode passed them (unlikely)
    if '\0' in line:
        print(f"Null byte found at line {i+1}")
        found_garbage = True
        break
    clean_lines.append(line)

if found_garbage:
    print(f"Truncating to {len(clean_lines)} lines.")
    with open(target, 'w', encoding='utf-8') as f:
        f.writelines(clean_lines)
        f.write('\n') # Ensure newline
else:
    print("No garbage chars found via replacement check.")
    # Maybe check for sudden change in indentation or weird syntax?
    # Or maybe search for 'def create_context_menu' and see if it looks wrong.

# Append extension (only if we think we cleaned it, or strictly if we found the split point)
# But wait, create_context_menu might already be in 'clean_lines' if it was valid utf8 but logic was corrupted?
# The corrupted part was likely the result of Type >> (UTF16).
# So replacement char check IS the way to go.

# Append extension
with open(extension, 'r', encoding='utf-8') as ext:
    new_code = ext.read()
    
# Avoid appending duplicate if it's already there and valid
if "def create_context_menu" not in "".join(clean_lines):
    with open(target, 'a', encoding='utf-8') as f:
        f.write(new_code)
    print("Appended extension.")
else:
    print("create_context_menu already present, not appending.")
