"""
Speech-to-Text (STT) module.
Supports both local Whisper.cpp and OpenAI Whisper API.
"""

import os
import subprocess
import tempfile
import wave
import struct
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
            language: Language code (optional, e.g., 'en', 'en-US', 'en-GB', 'hi')
        
        Returns:
            Transcribed text or None if failed
        """
        logger.debug(f"Transcribing audio file: {audio_file_path}")
        
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None
        
        file_size = os.path.getsize(audio_file_path)
        logger.debug(f"Audio file size: {file_size} bytes")
        
        if file_size < 1000:  # Less than 1KB is likely too small
            logger.warning(f"Audio file too small: {file_size} bytes")
            return None
        
        # Get language codes from configuration (supports multiple, comma-separated)
        # Note: OpenAI Whisper API only accepts ISO-639-1 base language codes (e.g., 'en', 'hi')
        # Region codes (e.g., 'en-US', 'en-IN') are converted to base codes
        def normalize_language_code(lang_code: Optional[str]) -> Optional[str]:
            """Convert language code to ISO-639-1 format (base language only)."""
            if not lang_code:
                return None
            # Extract base language code (part before hyphen)
            # e.g., 'en-US' -> 'en', 'en-IN' -> 'en', 'hi' -> 'hi'
            base_code = lang_code.strip().split('-')[0].split('_')[0].lower()
            # Validate it's a 2-letter code (ISO-639-1)
            if len(base_code) == 2:
                return base_code
            # If it's already a valid code, return as-is
            return base_code if base_code else None
        
        language_codes = None
        if language is None:
            stt_language = os.getenv("STT_LANGUAGE", None)
            if stt_language:
                # Support comma-separated language codes for multiple accents
                raw_codes = [lang.strip() for lang in stt_language.split(",") if lang.strip()]
                # Normalize to ISO-639-1 format (base language codes)
                language_codes = [normalize_language_code(code) for code in raw_codes if normalize_language_code(code)]
                if language_codes:
                    language = language_codes[0]  # Use first as primary
                    if len(language_codes) > 1:
                        logger.debug(f"Using primary language: {language}, fallbacks: {language_codes[1:]}")
                    else:
                        logger.debug(f"Using configured language: {language}")
                else:
                    logger.warning(f"No valid language codes found in STT_LANGUAGE: {stt_language}")
        
        # Try OpenAI API first if available and enabled
        if self.use_openai_api and self.openai_client:
            is_online = await self.network_monitor.is_online()
            if is_online:
                # Try each language code in order if multiple are specified
                languages_to_try = language_codes if language_codes else [language] if language else [None]
                last_error = None
                
                for lang_to_try in languages_to_try:
                    try:
                        with open(audio_file_path, "rb") as audio_file:
                            # Use deployment name for Azure, model name for standard OpenAI
                            if self.use_azure:
                                model_name = os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT", "whisper-1")
                            else:
                                model_name = "whisper-1"
                            
                            transcript_params = {
                                "model": model_name,
                                "file": audio_file,
                                "prompt": "This is a voice command to a personal assistant named Jarvis. The user is asking questions or giving commands. Common commands include: what is the weather, what time is it, do I have meetings, stop, etc. Transcribe exactly what the user says."
                            }
                            if lang_to_try:
                                transcript_params["language"] = lang_to_try
                            
                            transcript = self.openai_client.audio.transcriptions.create(**transcript_params)
                        
                        provider = "Azure OpenAI API" if self.use_azure else "OpenAI API"
                        lang_info = f" (language: {lang_to_try})" if lang_to_try else " (auto-detect)"
                        logger.info(f"Transcription successful ({provider}{lang_info})")
                        return transcript.text
                    except Exception as e:
                        last_error = e
                        # If this isn't the last language to try, continue to next
                        if lang_to_try != languages_to_try[-1]:
                            logger.debug(f"Transcription with {lang_to_try} failed, trying next language: {e}")
                            continue
                        # If this is the last language or only one, use the error
                
                # If we get here, all languages failed
                error_msg = str(last_error) if last_error else "Unknown error"
                # Check for invalid API key errors
                if "401" in error_msg or "invalid_api_key" in error_msg.lower() or "Incorrect API key" in error_msg:
                    logger.warning(f"OpenAI Whisper API key is invalid. Disabling OpenAI API and using local Whisper only.")
                    # Disable OpenAI API for future requests if key is invalid
                    self.use_openai_api = False
                    self.openai_client = None
                else:
                    logger.warning(f"OpenAI Whisper API failed with all languages: {error_msg}, falling back to local")
        
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
        language: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2
    ) -> Optional[str]:
        """
        Transcribe audio bytes to text.
        Creates a temporary WAV file with proper headers for processing.
        
        Args:
            audio_bytes: Raw PCM audio data as bytes
            language: Language code (optional, e.g., 'en', 'en-US', 'en-GB', 'hi', 'es')
                      If None, uses STT_LANGUAGE from .env or auto-detects
            sample_rate: Audio sample rate (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            sample_width: Sample width in bytes (default: 2 for 16-bit)
        
        Returns:
            Transcribed text or None if failed
        """
        logger.info(f"Transcribing audio bytes: {len(audio_bytes)} bytes, sample_rate={sample_rate}, channels={channels}, sample_width={sample_width}")
        
        # Check if audio is too short (less than 0.1 seconds at 16kHz, 16-bit mono = 3200 bytes)
        min_audio_size = sample_rate * sample_width * channels * 0.1  # 0.1 seconds minimum
        if len(audio_bytes) < min_audio_size:
            logger.warning(f"Audio too short: {len(audio_bytes)} bytes (minimum: {min_audio_size:.0f} bytes for 0.1s)")
            return None
        
        # Note: language parsing and fallback is handled in transcribe() method
        # We pass language=None here to let transcribe() handle STT_LANGUAGE parsing
        # This ensures the fallback mechanism works correctly
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            try:
                # Create proper WAV file with headers
                with wave.open(tmp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_bytes)
                
                logger.debug(f"Created temporary WAV file: {tmp_file.name} ({os.path.getsize(tmp_file.name)} bytes)")
                
                # Pass language=None to let transcribe() handle STT_LANGUAGE parsing and fallback
                result = await self.transcribe(tmp_file.name, language)
                
                if result:
                    logger.info(f"Transcription successful: '{result[:100]}...' ({len(result)} chars)" if len(result) > 100 else f"Transcription successful: '{result}' ({len(result)} chars)")
                else:
                    logger.warning("Transcription returned None or empty string")
                
                return result
            except Exception as e:
                logger.error(f"Error in transcribe_bytes: {e}", exc_info=True)
                return None
            finally:
                if os.path.exists(tmp_file.name):
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

