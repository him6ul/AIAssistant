"""
Speech-to-Text (STT) module.
Supports both local Whisper.cpp and OpenAI Whisper API.
"""

import os
import subprocess
import tempfile
from typing import Optional

# Try to import whisper, but make it optional
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

from openai import OpenAI
from app.network import get_network_monitor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class STTEngine:
    """
    Speech-to-Text engine supporting local Whisper and OpenAI Whisper API.
    """
    
    def __init__(
        self,
        model: str = "base",
        use_openai_api: bool = True,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize STT engine.
        
        Args:
            model: Whisper model size (tiny, base, small, medium, large)
            use_openai_api: Prefer OpenAI API when online
            openai_api_key: OpenAI API key (optional)
        """
        self.model = model
        self.use_openai_api = use_openai_api
        self.openai_client: Optional[OpenAI] = None
        
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Load local Whisper model (if available)
        self.local_model = None
        if WHISPER_AVAILABLE:
            try:
                logger.info(f"Loading local Whisper model: {model}")
                self.local_model = whisper.load_model(model)
                logger.info("Local Whisper model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load local Whisper model: {e}")
                self.local_model = None
        else:
            logger.info("Whisper not available, will use OpenAI API or alternative methods")
        
        self.network_monitor = get_network_monitor()
    
    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (optional, auto-detect if None)
        
        Returns:
            Transcribed text or None if failed
        """
        # Try OpenAI API first if available and enabled
        if self.use_openai_api and self.openai_client:
            is_online = await self.network_monitor.is_online()
            if is_online:
                try:
                    with open(audio_file_path, "rb") as audio_file:
                        transcript = self.openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language=language
                        )
                    logger.info("Transcription successful (OpenAI API)")
                    return transcript.text
                except Exception as e:
                    logger.warning(f"OpenAI Whisper API failed: {e}, falling back to local")
        
        # Fallback to local Whisper
        if self.local_model:
            try:
                result = self.local_model.transcribe(audio_file_path, language=language)
                logger.info("Transcription successful (local Whisper)")
                return result["text"]
            except Exception as e:
                logger.error(f"Local Whisper transcription failed: {e}")
                return None
        
        logger.error("No STT engine available")
        return None
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio bytes to text.
        Creates a temporary file for processing.
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language code (optional)
        
        Returns:
            Transcribed text or None if failed
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            try:
                tmp_file.write(audio_bytes)
                tmp_file.flush()
                return self.transcribe(tmp_file.name, language)
            finally:
                os.unlink(tmp_file.name)


# Global STT instance
_stt_engine: Optional[STTEngine] = None


def get_stt_engine() -> STTEngine:
    """
    Get or create the global STT engine instance.
    
    Returns:
        STTEngine instance
    """
    global _stt_engine
    if _stt_engine is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        _stt_engine = STTEngine(
            model=os.getenv("WHISPER_MODEL", "base"),
            use_openai_api=True,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    return _stt_engine

