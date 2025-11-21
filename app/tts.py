"""
Text-to-Speech (TTS) module.
Uses pyttsx3 for local TTS on macOS.
"""

import pyttsx3
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TTSEngine:
    """
    Text-to-Speech engine using pyttsx3 (local macOS voices).
    """
    
    def __init__(
        self,
        rate: int = 150,
        volume: float = 0.8,
        voice_id: Optional[str] = None
    ):
        """
        Initialize TTS engine.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Specific voice ID (optional, uses system default if None)
        """
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # Set voice if specified
            if voice_id:
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if voice_id in voice.id:
                        self.engine.setProperty('voice', voice.id)
                        logger.info(f"Using voice: {voice.name}")
                        break
            
            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            wait: Whether to wait for speech to complete
        
        Returns:
            True if successful, False otherwise
        """
        if not self.engine:
            logger.error("TTS engine not available")
            return False
        
        try:
            self.engine.say(text)
            if wait:
                self.engine.runAndWait()
            else:
                self.engine.startLoop(False)
            logger.debug(f"Spoke: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return False
    
    def save_to_file(self, text: str, filename: str) -> bool:
        """
        Save speech to audio file.
        
        Args:
            text: Text to convert
            filename: Output filename
        
        Returns:
            True if successful, False otherwise
        """
        if not self.engine:
            logger.error("TTS engine not available")
            return False
        
        try:
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait()
            logger.info(f"Saved speech to: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save speech: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """
        Get list of available voices.
        
        Returns:
            List of voice information dicts
        """
        if not self.engine:
            return []
        
        voices = []
        for voice in self.engine.getProperty('voices'):
            voices.append({
                "id": voice.id,
                "name": voice.name,
                "languages": getattr(voice, 'languages', [])
            })
        return voices


# Global TTS instance
_tts_engine: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    """
    Get or create the global TTS engine instance.
    
    Returns:
        TTSEngine instance
    """
    global _tts_engine
    if _tts_engine is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        _tts_engine = TTSEngine(
            rate=int(os.getenv("TTS_RATE", "150")),
            volume=float(os.getenv("TTS_VOLUME", "0.8"))
        )
    return _tts_engine

