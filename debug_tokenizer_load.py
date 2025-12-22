from transformers import NllbTokenizer
import os

model_dir = r"C:\Users\sai\jp\models\nllb_600m_v1"

print(f"Testing load from: {model_dir}")
print(f"Files: {os.listdir(model_dir)}")

try:
    print("Attempting to load via NllbTokenizer.from_pretrained(model_dir)...")
    tokenizer = NllbTokenizer.from_pretrained(model_dir, local_files_only=True)
    print("SUCCESS! Loaded tokenizer.")
    print(tokenizer.encode("Hello world"))
except Exception as e:
    print(f"FAILED (local_files_only=True): {e}")

try:
    print("Attempting to load via NllbTokenizer.from_pretrained(model_dir) (allowing network)...")
    tokenizer = NllbTokenizer.from_pretrained(model_dir)
    print("SUCCESS! Loaded tokenizer (network allowed).")
    print(tokenizer.encode("Hello world"))
except Exception as e:
    print(f"FAILED (network fallback): {e}")
