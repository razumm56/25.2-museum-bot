import asyncio

class TTS:
    def __init__(self):
        pass

    async def generate_voice_message(self, text: str):
        await asyncio.sleep(1)
        return 'temp/voice_message.mp3'