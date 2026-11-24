import asyncio
import os
import azure.cognitiveservices.speech as speechsdk

class convert:
    def __init__(self, texttoconvert, ws=None, loop=None):
        self.texttoconvert = texttoconvert
        self.ws = ws
        self.loop = loop
        self.avatar_speaking = False

    def send_avatar_signal(self, signal):
        print(f"🦜 (DEBUG) send_avatar_signal called with: {signal}")
        try:
            if self.ws and self.loop:
                asyncio.run_coroutine_threadsafe(self.ws.send(signal), self.loop)
                print(f"🦜 Signal '{signal}' sent to avatar!")
            else:
                print("🦜 (DEBUG) ws or loop missing! ws:", self.ws, "loop:", self.loop)
        except Exception as e:
            print(f"Avatar WebSocket send failed: {e}")

    def readout(self):
        # Azure Speech Config
        speech_config = speechsdk.SpeechConfig(
            subscription=os.environ.get("SPEECH_KEY"),
            region=os.environ.get("SPEECH_REGION")
        )
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        speech_config.speech_synthesis_voice_name = 'en-US-JennyNeural'
        synthesizer = speechsdk.SpeechSynthesizer(speech_config, audio_config)

        text = str(self.texttoconvert)
        print(f"🔈 Speaking: {text}")

        # 🛑 Ensure avatar doesn't stop too early
        avatar_start_sent = False
        synthesis_done = asyncio.Event()

        def on_synthesis_started(evt):
            nonlocal avatar_start_sent
            if not avatar_start_sent:
                self.send_avatar_signal("start")
                avatar_start_sent = True

        def on_synthesis_completed(evt):
            print("✅ Synthesis playback complete.")
            self.send_avatar_signal("stop")
            synthesis_done.set()

        def on_canceled(evt):
            print("❌ Synthesis canceled.")
            self.send_avatar_signal("stop")
            synthesis_done.set()

        # 🔗 Hook up Azure callbacks
        synthesizer.synthesis_started.connect(on_synthesis_started)
        synthesizer.synthesis_completed.connect(on_synthesis_completed)
        synthesizer.synthesis_canceled.connect(on_canceled)

        try:
            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print("📣 Audio playback successful.")
            elif result.reason == speechsdk.ResultReason.Canceled:
                details = result.cancellation_details
                print(f"⚠️ Playback canceled: {details.reason}")
                if details.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {details.error_details}")
        except Exception as e:
            print(f"💥 TTS Error: {e}")
            self.send_avatar_signal("stop")  # Just in case it didn't complete

        print("🛑 Avatar speaking session ended.")

if __name__ == "__main__":
    convert("Hello, I am Julie. Testing one, two, three.").readout()