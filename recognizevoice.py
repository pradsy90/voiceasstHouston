import azure.cognitiveservices.speech as speechsdk
import speech2text
import texttospeech
import chat
import json
import winsound
import websockets
import asyncio
import datetime
from agent import is_tasky, agent_run

class recognizevoice():
    def read_config_file(self, file_path):
        with open(file_path, 'r') as file:
            config_data = json.load(file)
        return config_data

    def __init__(self, glblvrbllist, glblvrbldict):
        self.secdelay = 5
        self.question = glblvrbldict['question']
        self.answer = glblvrbldict['answer']
        self.transcript = glblvrbldict['transcript']

    # Send commands to avatar WebSocket server (port 8766)
    def send_to_avatar_server(self, text, wait=True):
        async def inner():
            try:
                async with websockets.connect("ws://localhost:8766") as websocket:
                    await websocket.send(text)
                    if wait:
                        await asyncio.wait_for(websocket.recv(), timeout=180)
            except Exception as e:
                print(f"Could not send to avatar server: {e}")
        asyncio.run(inner())

    def recog_kywrd(self, glblvrbllist, glblvrbldict):
        try:
            # Speak out that voice recognition is enabled
            speechregenabled = texttospeech.convert("Voice Recognition enabled")
            speechregenabled.readout()

            model = speechsdk.KeywordRecognitionModel("C:\\cutover\\HeyJulie_11222026.table")
            keyword_recognizer = speechsdk.KeywordRecognizer()
            done = False

            # Event Handlers
            def recognized_cb(evt):
                result = evt.result
                if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                    print("🎯 Keyword recognized!")
                nonlocal done
                done = True

            def canceled_cb(evt):
                print(f"🚫 Canceled: {evt}")
                nonlocal done
                done = True

            keyword_recognizer.recognized.connect(recognized_cb)
            keyword_recognizer.canceled.connect(canceled_cb)

            configpath = "C:\\Users\\pradhip.swaminathan\\IdeaProjects\\voiceasstHouston\\settings.config"
            config = self.read_config_file(configpath)
            master = config.get('Masters_Name')
            assistant = config.get('Assistants_Name')
            prompt = config.get('Prompt')
            num_questions = int(config.get('NumQuestions', 5))

            recogctr = 0
            glblvrbldict["Process3"] = f"🎧 Voice Assistant ready for {num_questions} questions"

            while recogctr < num_questions:
                qnum = recogctr + 1
                try:
                    print(f"\n🔁 [{datetime.datetime.now()}] Listening for keyword (#{qnum})...")
                    result = keyword_recognizer.recognize_once_async(model).get()

                    if result.reason != speechsdk.ResultReason.RecognizedKeyword:
                        print("⚠️ Keyword NOT recognized. Retrying...")
                        continue

                    # Ding-dong
                    winsound.PlaySound('C:\\Users\\pradhip.swaminathan\\IdeaProjects\\voiceasstHouston\\ding.wav',
                                       winsound.SND_FILENAME | winsound.SND_ASYNC)

                    glblvrbldict['Process3'] = f"🎤 Listening to Question #{qnum}"
                    print(f"🎙️ Recording for Q{qnum}...")

                    # Record question
                    strrecgzd = (speech2text.from_mic() or "").strip()
                    if not strrecgzd:
                        print("⚠️ Didn't catch a question. Say the wake word again.")
                        continue

                    print(f"📝 Heard: {strrecgzd}")
                    self.question += f"\n{master} : {strrecgzd}"
                    self.transcript += f"\n\n{master} : {strrecgzd}"

                    # Get the answer (one variable, set on both paths)
                    if is_tasky(strrecgzd):
                        print("🧩 Using agent...")
                        answertoqn = agent_run(strrecgzd, glblvrbldict)
                    else:
                        print("🤖 Asking OpenAI...")
                        answertoqn = chat.return_answer(prompt + " " + strrecgzd + "</Question>")

                    self.answer += f"\n{answertoqn}"
                    self.transcript += f"\n\n{assistant} : {answertoqn}"

                    # Send to avatar server
                    self.send_to_avatar_server(f"text:Answering question #{qnum}\n{answertoqn}")

                    # Update shared memory
                    glblvrbllist.append(strrecgzd)
                    glblvrbldict['question'] = self.question
                    glblvrbldict['answer'] = self.answer
                    glblvrbldict['transcript'] = self.transcript

                    print(f"✅ Finished Q{qnum}")
                    recogctr += 1

                except Exception as e:
                    errmsg = f"💥 Error in loop: {e}"
                    print(errmsg)
                    glblvrbldict['Process3'] = errmsg
                    # Tell the user, and count the question so a persistent error can't loop forever
                    self.send_to_avatar_server(f"text:Sorry, I ran into a problem with that question.")
                    recogctr += 1
                    continue

            glblvrbldict['Process3'] = "🎉 All questions answered. Ending recognition."
            glblvrbldict['Shutdown'] = True
            glblvrbldict['transcript'] += "\nAll Qns answered.\nEnd of Transcript."

        except Exception as e:
            error_msg = f"❌ Top-level recognition error: {str(e)}"
            glblvrbldict['Process3'] = error_msg
            print(error_msg)