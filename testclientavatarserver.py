import asyncio, websockets

async def main():
    async with websockets.connect("ws://localhost:8766") as ws:
        await ws.send("text:Hello, this is a test of the avatar. See Cpt.Jack spinning mate.")

asyncio.run(main())