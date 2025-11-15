import os
import tempfile
from pathlib import Path
import sys
import assemblyai as aai
from config.settings import STT_CONFIG

sys.path.append(str(Path(__file__).parent.parent))


class STTManager:
    """Менеджер для преобразования речи в текст (AssemblyAI)"""
    
    def __init__(self):
        self.api_key = STT_CONFIG.get('api_key')
        aai.settings.api_key = self.api_key
        
        self.config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best,
            language_code="ru"
        )
        self.transcriber = aai.Transcriber(config=self.config)
        print(f"STT initialized with AssemblyAI")
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Преобразование аудиофайла в текст"""
        try:
            transcript = self.transcriber.transcribe(audio_file_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise RuntimeError(f"Transcription failed: {transcript.error}")
            
            return transcript.text.strip() if transcript.text else ""
        
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            raise
    
    async def transcribe_telegram_voice(self, voice_file) -> str:
        """Преобразование голосового сообщения Telegram в текст"""
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            temp_path = temp_file.name
            await voice_file.download_to_drive(temp_path)
        
        try:
            text = await self.transcribe_audio(temp_path)
            return text.strip()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
