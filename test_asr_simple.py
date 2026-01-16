import os
import sys
import numpy as np
import sherpa_onnx

def test_asr():
    model_path = r"C:\Users\sai\jp\models\sensevoice_sherpa"
    model_file = os.path.join(model_path, "model.int8.onnx")
    if not os.path.exists(model_file):
        model_file = os.path.join(model_path, "model.onnx")
    tokens_file = os.path.join(model_path, "tokens.txt")
    
    print(f"Testing with model: {model_file}")
    print(f"Tokens: {tokens_file}")
    
    if not os.path.exists(model_file) or not os.path.exists(tokens_file):
        print("Model files missing!")
        return

    try:
        recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=model_file,
            tokens=tokens_file,
            use_itn=True,
            language="auto",
            num_threads=4
        )
        print("Recognizer initialized successfully.")
        
        # Create a dummy silent audio (1 second at 16k)
        audio = np.zeros(16000, dtype=np.float32)
        stream = recognizer.create_stream()
        stream.accept_waveform(16000, audio)
        recognizer.decode_stream(stream)
        
        print(f"Transcription result: '{stream.result.text}'")
        print("Test PASSED")
    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_asr()
