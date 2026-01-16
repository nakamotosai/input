import sys
import os
sys.path.append(os.getcwd())
try:
    import tts_worker
    print("Import success")
    tts_worker.say("こんにちは、テストです。")
    import time
    time.sleep(5)
    print("Done")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
