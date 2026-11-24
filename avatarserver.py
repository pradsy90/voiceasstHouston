
# import asyncio
# import websockets
# import sys
# import webbrowser
# import os
# from texttospeech import convert
#
# connected = set()
# glblvrbldict = None  # ✅ Injected at launch
#
# # top-level
# shutdown_event = asyncio.Event()
# server_avatar = None
# server_cmd = None
#
# async def handle_avatar(websocket):
#     print("🌐 Avatar connected via WebSocket.")
#     connected.add(websocket)
#     try:
#         async for message in websocket:
#             print(f"🦜 Message from browser: {message}")
#     except websockets.exceptions.ConnectionClosed:
#         print("❌ Browser disconnected.")
#     finally:
#         connected.remove(websocket)
#
# async def handle_command(websocket):
#     global glblvrbldict
#     print("⚡ Command client connected.")
#     try:
#         async for message in websocket:
#             print(f"⚡ Command received: {message}")
#
#             if message == "shutdown":
#                 # notify UI (optional)
#                 print ("GOT A SHUTDOWN HERE! AYE AYE AYE")
#                 for ws in list(connected):
#                     try: await ws.send("text:Server shutting down…")
#                     except: pass
#                 shutdown_event.set()
#                 continue
#
#             # Parse optional question number
#             if "|" in message:
#                 command, qnum = message.split("|", 1)
#                 print ("Did a message split")
#             else:
#                 command = message
#                 qnum = None
#
#             if not connected:
#                 print("🛑 No browser connected! Ignoring command.")
#                 continue
#
#             ws = next(iter(connected))
#
#             if command == "start":
#                 await ws.send("start")
#                 if glblvrbldict and qnum:
#                     glblvrbldict['Process4'] = f"Avatar answering Question {qnum}"
#                 print(f"🎭 Avatar answering Question {qnum}")
#             elif command == "stop":
#                 await ws.send("stop")
#             elif command.startswith("text:"):
#                 await ws.send(command)
#
#
#
#             # Let TTS do the heavy lifting
#             loop = asyncio.get_running_loop()
#             tts = convert(texttoconvert=message, ws=ws, loop=loop)
#             #await tts.readout()
#             await asyncio.get_event_loop().run_in_executor(None, tts.readout)
#
#     except websockets.exceptions.ConnectionClosed:
#         print("⚡ Command client disconnected.")
#
# def open_avatar_html():
#     path = os.path.abspath("avatar.html")
#     url = "file://" + path.replace("\\", "/")
#     print(f"🧭 Opening avatar HTML: {url}")
#     webbrowser.open(url, new=1)
#
# async def main():
#     global server_avatar, server_cmd
#     print("🏴‍☠️ Starting server on ws://localhost:8765 and 8766...")
#     server_avatar = await websockets.serve(handle_avatar, "localhost", 8765)
#     server_cmd    = await websockets.serve(handle_command, "localhost", 8766)
#     open_avatar_html()
#     print("📣 Type text and press Enter to speak (Ctrl+C to quit).")
#
#     # Replace blocking stdin loop with a wait on shutdown_event
#     try:
#         await shutdown_event.wait()
#     finally:
#         print("🧹 Shutting down WebSocket servers…")
#         server_avatar.close(); server_cmd.close()
#         await server_avatar.wait_closed(); await server_cmd.wait_closed()
#
#     try:
#         while True:
#             text = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
#             text = text.strip()
#             if not text:
#                 continue
#             if not connected:
#                 print("🛑 No avatar connected! Try again after browser connects.")
#                 continue
#
#             ws = next(iter(connected))
#             print(f"🗣️ Sending to TTS: '{text}'")
#             await ws.send("text:" + text)
#             print(f"📤 Sent to Avatar UI: {text}")
#             loop = asyncio.get_running_loop()
#             tts = convert(texttoconvert=text, ws=ws, loop=loop)
#             #await tts.readout()
#             await asyncio.get_event_loop().run_in_executor(None, tts.readout)
#     except KeyboardInterrupt:
#         print("\n⛵ Server shutting down. Bye, matey!")
#         server_avatar.close()
#         server_cmd.close()
#         await server_avatar.wait_closed()
#         await server_cmd.wait_closed()
#
# # ✅ Launcher that injects global dictionary
# def launch_avatar_with_shared_dict(shared_dict):
#     global glblvrbldict
#     glblvrbldict = shared_dict
#     asyncio.run(main())
# */

import asyncio
import os
import webbrowser

import websockets

from texttospeech import convert

SPEAK_HEADER = False  # True = Jenny also reads "Answering question #N"

connected = set()
glblvrbldict = None  # Injected at launch

shutdown_event = asyncio.Event()
speech_lock = asyncio.Lock()  # one answer spoken at a time
server_avatar = None
server_cmd = None


async def handle_avatar(websocket):
    print("🌐 Avatar connected via WebSocket.")
    connected.add(websocket)
    try:
        async for message in websocket:
            print(f"🦜 Message from browser: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Browser disconnected.")
    finally:
        connected.discard(websocket)


async def handle_command(websocket):
    global glblvrbldict
    print("⚡ Command client connected.")
    try:
        async for message in websocket:
            print(f"⚡ Command received: {message[:80]}")

            if message == "shutdown":
                print("🛑 Shutdown requested; waiting for speech to finish...")
                async with speech_lock:
                    shutdown_event.set()
                continue

            if not connected:
                print("🛑 No browser connected! Ignoring command.")
                continue

            ws = next(iter(connected))
            loop = asyncio.get_running_loop()

            # start / stop (optionally "start|<qnum>")
            command, _, qnum = message.partition("|")
            if command in ("start", "stop"):
                await ws.send(command)
                if command == "start" and glblvrbldict is not None and qnum:
                    glblvrbldict["Process4"] = f"Avatar answering Question {qnum}"
                continue

            # Everything else is speech: "text:<words>" or plain text
            display = message[len("text:"):] if message.startswith("text:") else message

            # Optionally skip the "Answering question #N" header when speaking
            header, _, body = display.partition("\n")
            if not SPEAK_HEADER and header.startswith("Answering question") and body:
                to_speak = body
            else:
                to_speak = display

            async with speech_lock:
                await ws.send("text:" + display)
                tts = convert(texttoconvert=to_speak, ws=ws, loop=loop)
                await loop.run_in_executor(None, tts.readout)
                await websocket.send("done")

    except websockets.exceptions.ConnectionClosed:
        print("⚡ Command client disconnected.")


def open_avatar_html():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar.html")
    url = "file://" + path.replace("\\", "/")
    print(f"🧭 Opening avatar HTML: {url}")
    webbrowser.open(url, new=1)


async def main():
    global server_avatar, server_cmd
    print("🏴‍☠️ Starting server on ws://localhost:8765 and 8766...")
    server_avatar = await websockets.serve(handle_avatar, "localhost", 8765)
    server_cmd = await websockets.serve(handle_command, "localhost", 8766)
    open_avatar_html()
    print("📣 Avatar server ready (Ctrl+C to quit).")

    try:
        await shutdown_event.wait()
    finally:
        print("🧹 Shutting down WebSocket servers…")
        server_avatar.close()
        server_cmd.close()
        await server_avatar.wait_closed()
        await server_cmd.wait_closed()


# Launcher that injects the shared dictionary (used by startjulie.py)
def launch_avatar_with_shared_dict(shared_dict):
    global glblvrbldict
    glblvrbldict = shared_dict
    asyncio.run(main())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛵ Server shutting down. Bye, matey!")