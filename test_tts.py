import asyncio
import edge_tts

async def main():
    print("Starting...")
    communicate = edge_tts.Communicate('test', 'en-US-AriaNeural')
    async for chunk in communicate.stream():
        pass
    print('done')

if __name__ == "__main__":
    asyncio.run(main())
