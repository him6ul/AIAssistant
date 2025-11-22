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

from openai import OpenAI, AzureOpenAI
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
        openai_api_key: Optional[str] = None,
        use_azure: bool = False,
        azure_endpoint: Optional[str] = None,
        azure_api_version: str = "2024-02-15-preview"
    ):
        """
        Initialize STT engine.
        
        Args:
            model: Whisper model size (tiny, base, small, medium, large)
            use_openai_api: Prefer OpenAI API when online
            openai_api_key: OpenAI API key (or Azure OpenAI API key)
            use_azure: Whether to use Azure OpenAI
            azure_endpoint: Azure OpenAI endpoint URL
            azure_api_version: Azure OpenAI API version
        """
        self.model = model
        self.use_openai_api = use_openai_api
        self.openai_client: Optional[OpenAI] = None
        self.use_azure = use_azure
        self.azure_endpoint = azure_endpoint
        self.azure_api_version = azure_api_version
        
        if openai_api_key:
            try:
                if use_azure and azure_endpoint:
                    # Use Azure OpenAI
                    self.openai_client = AzureOpenAI(
                        api_key=openai_api_key,
                        api_version=azure_api_version,
                        azure_endpoint=azure_endpoint
                    )
                    logger.info(f"Initialized Azure OpenAI STT client: {azure_endpoint}")
                else:
                    # Use standard OpenAI
                    self.openai_client = OpenAI(api_key=openai_api_key)
                    logger.info("Initialized standard OpenAI STT client")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Will use local Whisper only.")
                self.openai_client = None
                self.use_openai_api = False
        
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
                        # Use deployment name for Azure, model name for standard OpenAI
                        if self.use_azure:
                            model_name = os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT", "whisper-1")
                        else:
                            model_name = "whisper-1"
                        transcript = self.openai_client.audio.transcriptions.create(
                            model=model_name,
                            file=audio_file,
                            language=language
                        )
                    provider = "Azure OpenAI API" if self.use_azure else "OpenAI API"
                    logger.info(f"Transcription successful ({provider})")
                    return transcript.text
                except Exception as e:
                    error_msg = str(e)
                    # Check for invalid API key errors
                    if "401" in error_msg or "invalid_api_key" in error_msg.lower() or "Incorrect API key" in error_msg:
                        logger.warning(f"OpenAI Whisper API key is invalid. Disabling OpenAI API and using local Whisper only.")
                        # Disable OpenAI API for future requests if key is invalid
                        self.use_openai_api = False
                        self.openai_client = None
                    else:
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
    
    async def transcribe_bytes(
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
                return await self.transcribe(tmp_file.name, language)
            finally:
                os.unlink(tmp_file.name)


# Global STT instance
_stt_engine: Optional[STTEngine] = None


def reset_stt_engine():
    """
    Reset the global STT engine instance to force reload from .env.
    Useful when .env file is updated.
    """
    global _stt_engine
    _stt_engine = None
    logger.info("STT engine instance reset - will reload on next access")


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
        # Force reload .env file to pick up latest changes
        load_dotenv(override=True)
        
        # Check if Azure OpenAI should be used
        use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        logger.info(f"Initializing STT engine with API key: {api_key[:10] if api_key else 'None'}...")
        
        _stt_engine = STTEngine(
            model=os.getenv("WHISPER_MODEL", "base"),
            use_openai_api=True,
            openai_api_key=api_key,
            use_azure=use_azure,
            azure_endpoint=azure_endpoint,
            azure_api_version=azure_api_version
        )
    return _stt_engine

