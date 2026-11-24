import sys
import os
import openai
import azure.cognitiveservices.speech as speechsdk

print("⚓ PYTHON EXECUTABLE:")
print(sys.executable)

print("\n📦 sys.path (module search locations):")
for p in sys.path:
    print(f"  - {p}")

print("\n🔍 Where are modules being loaded from?")
print(f"  - openai loaded from: {openai.__file__}")
print(f"  - azure speech loaded from: {speechsdk.__file__}")
