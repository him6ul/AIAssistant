"""
Voice listener with wake word detection and continuous listening.
"""

import asyncio
import pyaudio
import struct
from typing import Optional, Callable
from pvporcupine import create as create_porcupine, KEYWORDS
from app.stt import get_stt_engine
from app.llm_router import get_llm_router
from app.tts import get_tts_engine
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceListener:
    """
    Listens for wake word and processes voice commands.
    """
    
    def __init__(
        self,
        wake_word: str = "hey assistant",
        porcupine_access_key: Optional[str] = None,
        sensitivity: float = 0.5,
        callback: Optional[Callable] = None
    ):
        """
        Initialize voice listener.
        
        Args:
            wake_word: Wake word phrase
            porcupine_access_key: Porcupine access key
            sensitivity: Wake word detection sensitivity (0.0-1.0)
            callback: Callback function for voice commands
        """
        self.wake_word = wake_word
        self.porcupine_access_key = porcupine_access_key
        self.sensitivity = sensitivity
        self.callback = callback
        
        self.porcupine: Optional[Porcupine] = None
        self.audio_stream: Optional[pyaudio.PyAudio.Stream] = None
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        
        self.stt_engine = get_stt_engine()
        self.llm_router = get_llm_router()
        self.tts_engine = get_tts_engine()
        
        self._listening = False
        self._recording = False
    
    def _initialize_porcupine(self):
        """
        Initialize Porcupine wake word detector.
        """
        try:
            if not self.porcupine_access_key:
                logger.warning("Porcupine access key not provided, wake word detection disabled")
                return
            
            # Use Porcupine create() function with built-in keywords
            # Available built-in keywords: 'hey barista', 'hey google', 'hey siri', 'jarvis', 'porcupine', 'picovoice', etc.
            # For "hey assistant", we'll use 'jarvis' as a natural alternative
            # You can also use custom keyword files if needed
            keyword_to_use = "jarvis"  # Natural-sounding built-in keyword
            wake_word_lower = self.wake_word.lower()
            if "hey assistant" in wake_word_lower or "assistant" in wake_word_lower:
                keyword_to_use = "jarvis"  # Use 'jarvis' as natural alternative
            elif "hey" in wake_word_lower and "siri" in wake_word_lower:
                keyword_to_use = "hey siri"
            elif "hey" in wake_word_lower and "google" in wake_word_lower:
                keyword_to_use = "hey google"
            
            self.porcupine = create_porcupine(
                access_key=self.porcupine_access_key,
                keywords=[keyword_to_use],
                sensitivities=[self.sensitivity]
            )
            logger.info("Porcupine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            self.porcupine = None
    
    def _initialize_audio(self):
        """
        Initialize audio stream.
        """
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            sample_rate = self.porcupine.sample_rate if self.porcupine else 16000
            frame_length = self.porcupine.frame_length if self.porcupine else 512
            
            self.audio_stream = self.pyaudio_instance.open(
                rate=sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=frame_length
            )
            
            logger.info("Audio stream initialized")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.audio_stream = None
    
    async def _process_voice_command(self, audio_data: bytes):
        """
        Process voice command after wake word detection.
        
        Args:
            audio_data: Audio data bytes
        """
        logger.info("Processing voice command")
        
        try:
            # Transcribe audio
            text = self.stt_engine.transcribe_bytes(audio_data)
            
            if not text:
                logger.warning("No transcription result")
                return
            
            logger.info(f"Transcribed: {text}")
            
            # Get LLM response
            response = await self.llm_router.generate(
                prompt=text,
                system_prompt="You are a helpful personal assistant. Be concise and actionable."
            )
            
            content = response.get("content", "")
            mode = response.get("mode", "")
            
            # Speak response
            full_response = f"{content} [{mode}]" if mode else content
            self.tts_engine.speak(full_response)
            
            # Call callback if provided
            if self.callback:
                await self.callback(text, content, response)
        
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}")
            self.tts_engine.speak("I'm sorry, I encountered an error processing your request.")
    
    async def start(self):
        """
        Start voice listener.
        """
        if self._listening:
            logger.warning("Voice listener already running")
            return
        
        self._initialize_porcupine()
        self._initialize_audio()
        
        if not self.audio_stream:
            logger.error("Cannot start voice listener: audio stream not available")
            return
        
        self._listening = True
        logger.info("Voice listener started")
        
        # Simple wake word detection loop
        # In production, you'd use Porcupine's detection
        while self._listening:
            try:
                if self.porcupine:
                    # Read audio frame
                    pcm = self.audio_stream.read(
                        self.porcupine.frame_length,
                        exception_on_overflow=False
                    )
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    
                    # Check for wake word
                    keyword_index = self.porcupine.process(pcm)
                    
                    if keyword_index >= 0:
                        logger.info("Wake word detected!")
                        self.tts_engine.speak("Yes, how can I help?")
                        
                        # Record command (simplified - in production, use proper VAD)
                        await asyncio.sleep(1)  # Brief pause
                        
                        # Record for a few seconds
                        audio_frames = []
                        for _ in range(50):  # ~3 seconds at 16kHz
                            frame = self.audio_stream.read(512, exception_on_overflow=False)
                            audio_frames.append(frame)
                            await asyncio.sleep(0.06)
                        
                        audio_data = b''.join(audio_frames)
                        await self._process_voice_command(audio_data)
                
                else:
                    # No Porcupine, just listen continuously (simplified)
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Voice listener error: {e}")
                await asyncio.sleep(1)
    
    def stop(self):
        """
        Stop voice listener.
        """
        self._listening = False
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        
        if self.porcupine:
            self.porcupine.delete()
        
        logger.info("Voice listener stopped")


# Global listener instance
_listener: Optional[VoiceListener] = None


def get_voice_listener() -> VoiceListener:
    """
    Get or create the global voice listener instance.
    
    Returns:
        VoiceListener instance
    """
    global _listener
    if _listener is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        _listener = VoiceListener(
            wake_word=os.getenv("WAKE_WORD", "hey assistant"),
            porcupine_access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
            sensitivity=0.5
        )
    return _listener

