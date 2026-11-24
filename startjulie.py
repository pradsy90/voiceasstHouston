import string
import time
import recognizevoice
import multiprocessing
from datetime import datetime
import random
import re
import subprocess
import sys
import os
import json
import psutil

# 🧠 MAIN ENTRY POINT - Starts all subprocesses
def launchjulie(glblvrbllist, glblvrbldict):
    print("📦 Inside Launch Julie")
    glblvrbldict['Process1'] = 'Launch Julie Process 1 Started'
    glblvrbldict['Process2'] = 'Chat Transcription Window not yet started'
    glblvrbldict['Process3'] = 'Voice Recognition Assistant not yet started'
    glblvrbldict['Process4'] = 'Avatar Window not yet started'

    # 🔥 Launch Avatar Server
    print("🎭 Launching Avatar Face Server")
    p4 = multiprocessing.Process(target=basicavatarprocess, args=(glblvrbldict,))
    p4.start()
    glblvrbldict['Process4'] = f'Avatar Face Process launched (PID {p4.pid})'
    glblvrbldict['AvatarPID'] = p4.pid
    time.sleep(0.75)

    # 🎙️ Start Voice Assistant (Process 3)
    print("🎤 Opening Voice Assistant")
    glblvrbldict['Process3'] = 'Voice Assistant Starting...'
    p3 = multiprocessing.Process(target=callrecognize, args=(glblvrbllist, glblvrbldict))
    p3.start()

    # Wait for recognize process to define Filename
    wait_count = 0
    while 'Filename' not in glblvrbldict:
        time.sleep(0.5)
        wait_count += 1
        if wait_count > 30:
            print("❌ Timeout waiting for Filename from callrecognize()")
            return

    filename = glblvrbldict['Filename']
    transcript_path = os.path.join(
        "C:\\Users\\pradhip.swaminathan\\IdeaProjects\\voiceasstHouston\\chatlogs", f"{filename}.txt"
    )
    glblvrbldict['chattranscriptfile'] = transcript_path
    print(f"📄 Chat Transcript Path: {transcript_path}")

    try:
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write('Start of Transcript\n')
            print(f"✅ Transcript file created at: {transcript_path}")
    except Exception as e:
        print(f"❌ Error creating transcript file: {e}")

    glblvrbldict['Process2'] = 'Chat Transcription File Initialized'

    # 🖥️ Launch Chat UI (Streamlit)
    print("🧠 Opening Chat Assistant UI")
    p2 = multiprocessing.Process(target=basicchatwindowfull, args=(glblvrbllist, glblvrbldict))
    p2.start()
    glblvrbldict['Process2'] = f'Chat Assistant Window Started (PID {p2.pid})'

    # 📜 Background Transcript File Updater
    i=0
    while True:
        i=i+1
        time.sleep(15)
        glblvrbldict['Process1'] = f"Process 1 running for {i * 15} seconds"

        try:
            with open(transcript_path, "w+", encoding="utf-8") as f:
                f.write(glblvrbldict.get('transcript', ''))
                if i % 4 == 0:
                    glblvrbldict['Process1'] += ' | Transcript updated'
        except Exception as e:
            print(f"💥 Error writing transcript: {e}")


        if (glblvrbldict.get('Shutdown')):
         glblvrbldict['Process1'] = 'Shutdown signal received'
         break


    # 🧹 Wait for clean shutdown
    p2.join()
    print("✅ Chat Assistant Process Done")
    p3.join()
    print("✅ Voice Assistant Process Done")

    # stop Streamlit first (you already do)
    pid = glblvrbldict.get('StreamlitPID')
    if pid:
        try:
            psutil.Process(pid).terminate()
        except Exception as e:
            print(f"Streamlit terminate error: {e}")

    # tell avatar server to shutdown gracefully
    send_avatar_command("shutdown")             # <-- NEW
    p4.join(timeout=5)                           # don't block forever
    if p4.is_alive():
        print("Avatar didn’t stop in time; terminating…")
        p4.terminate()
#   p4.join()
    print("✅ Avatar Face Process Done")

    # 💀 Terminate Streamlit UI if it’s still alive
    try:
        pid = glblvrbldict.get('StreamlitPID')
        if pid:
            proc = psutil.Process(pid)
            proc.terminate()
            print(f"💀 Streamlit (PID {pid}) terminated.")
    except Exception as e:
        print(f"⚠️ Error during Streamlit cleanup: {e}")


# 🪟 Launch Chat UI
def basicchatwindowfull(glblvrbllist, glblvrbldict):
    transcript_file = glblvrbldict.get('chattranscriptfile', '')
    if not transcript_file:
        print("❌ No transcript file found in shared dictionary.")
        return

    streamlit_path = r"C:\Users\pradhip.swaminathan\AppData\Local\Programs\Python\Python313\Scripts\streamlit.exe"
    script_path = r"C:\Users\pradhip.swaminathan\IdeaProjects\voiceasstHouston\basicchatwindow.py"

    cmd = [
        streamlit_path,
        "run",
        script_path,
        "--server.port=8501",
        "--global.developmentMode=false",
        "--",
        f"--transcriptfile={transcript_file}"
    ]

    print("📋 COPY THIS IF NEEDED:\n" + " ".join(f'"{c}"' if ' ' in c else c for c in cmd) + "\n")

    proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    glblvrbldict['StreamlitPID'] = proc.pid
    glblvrbldict['Process2'] = f'Streamlit launched (PID {proc.pid})'
    print(f"🚀 Streamlit running on PID {proc.pid}")


# 🧠 Trigger Voice Recognition
def callrecognize(glblvrbllist, glblvrbldict):
    transn_code = generate_code()
    filename = datetime.now().strftime("%Y%m%d-%H%M%S")

    glblvrbldict['TransnCode'] = transn_code
    glblvrbldict['Filename'] = filename
    glblvrbldict['Process3'] = 'Voice Recognition Assistant Booted'

    glblvrbldict['question'] = ''
    glblvrbldict['answer'] = ''
    glblvrbldict['transcript'] = f"Transcript ID {transn_code}\n"

    glblvrbllist.append('')
    glblvrbllist.append('')

    recg = recognizevoice.recognizevoice(glblvrbllist, glblvrbldict)
    recg.recog_kywrd(glblvrbllist, glblvrbldict)


# 🎲 Random Transaction Code
def generate_code():
    while True:
        code = ['T']
        code += [random.choice(string.ascii_letters) for _ in range(2)]
        code += [random.choice(string.digits) for _ in range(2)]
        code += [random.choice(string.ascii_letters)]
        code += [random.choice(string.digits) for _ in range(2)]
        code += [random.choice(string.ascii_letters)]
        code += [random.choice(string.digits)]

        code_str = ''.join(code)
        if re.match(r'^T[A-Za-z]{2}\d{2}[A-Za-z]\d{2}[A-Za-z]\d$', code_str):
            return code_str


# 🎭 Avatar Face Launcher
def basicavatarprocess(glblvrbldict):
    print("🎭 Launching Avatar Face Server (Process 4)")
    glblvrbldict['Process4'] = 'Avatar Launch Starting'

    try:
        from avatarserver import launch_avatar_with_shared_dict
        asyncio_proc = multiprocessing.Process(target=launch_avatar_with_shared_dict, args=(glblvrbldict,))
        asyncio_proc.start()

        time.sleep(1)
        glblvrbldict['Process4'] = f"Avatar launched (PID {asyncio_proc.pid})"
        glblvrbldict['AvatarPID'] = asyncio_proc.pid
    except Exception as e:
        glblvrbldict['Process4'] = f"❌ Error launching avatar: {e}"

#Check this... I am not sure this is wokring. I am not sure this is being called.
def send_avatar_command(cmd: str):
    import asyncio, websockets
    async def _send():
        try:
            async with websockets.connect("ws://localhost:8766") as ws:
                await ws.send(cmd)
        except Exception as e:
            print(f"Avatar shutdown send failed: {e}")
    asyncio.run(_send())

# 🧨 MAIN ENTRY POINT
if __name__ == '__main__':
    glblvrbllist = multiprocessing.Manager().list()
    glblvrbldict = multiprocessing.Manager().dict()
    glblvrbldict['ProcessMain'] = "Running"

    p1 = multiprocessing.Process(target=launchjulie, args=(glblvrbllist, glblvrbldict))
    p1.start()

    for i in range(1, 11):
        time.sleep(20)
        glblvrbldict['ProcessMain'] = f"Running for {20 * i} seconds"
        print("🔄 Process Main: " + glblvrbldict['ProcessMain'])
        for proc_key in ['Process1', 'Process2', 'Process3', 'Process4']:
            print(f"📌 {proc_key}: {glblvrbldict.get(proc_key, 'Not started')}")


    p1.join()

