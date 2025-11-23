"""
Voice listener with wake word detection and continuous listening.
"""

import asyncio
import os
import pyaudio
import struct
from typing import Optional, Callable, List
from pvporcupine import create as create_porcupine, KEYWORDS
from dotenv import load_dotenv
from app.stt import get_stt_engine
from app.llm_router import get_llm_router
from app.tts import get_tts_engine
from app.commands.handler import get_command_handler
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv(override=True)


def get_stop_words() -> List[str]:
    """
    Get stop words from environment variable or return defaults.
    Same function as in handlers.py to ensure consistency.
    
    Returns:
        List of stop words/phrases
    """
    stop_words_env = os.getenv("STOP_WORDS", "").strip()
    if stop_words_env:
        # Split by comma and clean up
        stop_words = [word.strip().lower() for word in stop_words_env.split(",") if word.strip()]
        if stop_words:
            logger.debug(f"Using stop words from .env: {stop_words}")
            return stop_words
    
    # Default stop words if not configured
    default_stop_words = [
        "stop",
        "stop listening",
        "stop the assistant",
        "stop jarvis",
        "jarvis stop",
        "shut down",
        "exit",
        "quit"
    ]
    logger.debug(f"Using default stop words: {default_stop_words}")
    return default_stop_words


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
        self.sample_rate: int = 16000
        self.channels: int = 1
        self.sample_width: int = 2  # 16-bit = 2 bytes
        
        self.stt_engine = get_stt_engine()
        self.llm_router = get_llm_router()
        self.tts_engine = get_tts_engine()
        
        self._listening = False
        self._recording = False
        self._stop_check_interval = 0.5  # Check for stop commands every 0.5 seconds
        self._stop_listener_task: Optional[asyncio.Task] = None  # Background task for listening to stop commands
    
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
            # Map user's wake word to Porcupine's built-in keywords
            keyword_to_use = "jarvis"  # Default keyword
            wake_word_lower = self.wake_word.lower()
            
            # Check for "jarvis" first (most direct match)
            if "jarvis" in wake_word_lower:
                keyword_to_use = "jarvis"
            elif "hey assistant" in wake_word_lower or "assistant" in wake_word_lower:
                keyword_to_use = "jarvis"  # Use 'jarvis' as natural alternative
            elif "hey" in wake_word_lower and "siri" in wake_word_lower:
                keyword_to_use = "hey siri"
            elif "hey" in wake_word_lower and "google" in wake_word_lower:
                keyword_to_use = "hey google"
            elif "hey" in wake_word_lower and "barista" in wake_word_lower:
                keyword_to_use = "hey barista"
            else:
                # Default to jarvis for any unrecognized wake word
                keyword_to_use = "jarvis"
            
            logger.info(f"Using Porcupine keyword '{keyword_to_use}' for wake word '{self.wake_word}'")
            
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
            
            self.sample_rate = self.porcupine.sample_rate if self.porcupine else 16000
            frame_length = self.porcupine.frame_length if self.porcupine else 512
            
            self.audio_stream = self.pyaudio_instance.open(
                rate=self.sample_rate,
                channels=self.channels,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=frame_length
            )
            
            logger.info(f"Audio stream initialized (rate={self.sample_rate}Hz, channels={self.channels}, width={self.sample_width} bytes)")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.audio_stream = None
    
    async def _handle_stop_command(self):
        """
        Handle stop command - interrupt TTS and shut down gracefully.
        """
        logger.info("Stop command detected - shutting down voice listener")
        
        # Stop any ongoing TTS immediately
        try:
            self.tts_engine.stop_speaking()
            logger.info("Stopped ongoing TTS")
        except Exception as e:
            logger.warning(f"Error stopping TTS: {e}")
        
        # Set listening flag to False immediately to stop the loop
        self._listening = False
        logger.info("Set _listening flag to False")
        
        # Get user name from environment or use default
        user_name = os.getenv("USER_NAME", "Himanshu")
        goodbye_message = f"Goodbye {user_name}"
        
        # Run TTS in executor to avoid blocking async event loop
        # Ensure wait=True so it completes before we stop
        loop = asyncio.get_event_loop()
        logger.info(f"Speaking goodbye message: {goodbye_message}")
        result = await loop.run_in_executor(None, self.tts_engine.speak, goodbye_message, True)
        
        if result:
            logger.info("Goodbye message spoken successfully")
        else:
            logger.warning("Goodbye message may not have been spoken")
        
        # Stop the listener and clean up resources
        logger.info("Calling stop() method to clean up resources...")
        self.stop()
        logger.info("Voice listener stop() completed - exiting")
    
    async def _listen_for_stop_during_tts(self):
        """
        Background task that continuously listens for stop commands while TTS is speaking.
        This allows stop commands to work even when the assistant is speaking.
        Uses direct audio transcription without requiring wake word.
        """
        logger.debug("Started background stop listener")
        
        while self._listening:
            try:
                if not self.audio_stream:
                    await asyncio.sleep(0.5)
                    continue
                
                # Record a short audio sample (1 second) to check for stop commands
                # This works without requiring a wake word
                try:
                    audio_frames = []
                    # Record ~1 second of audio (16 frames at 0.06s each)
                    for _ in range(16):
                        try:
                            frame = self.audio_stream.read(512, exception_on_overflow=False)
                            audio_frames.append(frame)
                        except Exception as read_err:
                            logger.debug(f"Error reading frame: {read_err}")
                            break
                        await asyncio.sleep(0.06)
                    
                    if len(audio_frames) > 5:  # Only process if we got enough audio
                        audio_data = b''.join(audio_frames)
                        
                        # Transcribe the audio
                        text = await self.stt_engine.transcribe_bytes(
                            audio_data,
                            sample_rate=self.sample_rate,
                            channels=self.channels,
                            sample_width=self.sample_width
                        )
                        
                        if text:
                            text_lower = text.lower().strip()
                            stop_keywords = get_stop_words()
                            
                            # Check if any stop keyword is in the transcribed text
                            is_stop = any(keyword in text_lower for keyword in stop_keywords)
                            
                            if is_stop:
                                matched_keywords = [kw for kw in stop_keywords if kw in text_lower]
                                logger.info(f"Stop command detected during TTS: '{text}' (matched: {matched_keywords})")
                                await self._handle_stop_command()
                                break
                
                except Exception as read_error:
                    logger.debug(f"Error in stop listener: {read_error}")
                
                # Check every 1 second (after recording 1 second of audio)
                await asyncio.sleep(0.2)  # Small delay before next check
                
            except Exception as e:
                logger.debug(f"Error in stop listener: {e}")
                await asyncio.sleep(0.5)
        
        logger.debug("Background stop listener stopped")
    
    async def _process_voice_command(self, audio_data: bytes):
        """
        Process voice command after wake word detection.
        
        Args:
            audio_data: Audio data bytes
        """
        logger.info("Processing voice command")
        
        try:
            # Transcribe audio with proper format parameters
            text = await self.stt_engine.transcribe_bytes(
                audio_data,
                sample_rate=self.sample_rate,
                channels=self.channels,
                sample_width=self.sample_width
            )
            
            if not text:
                logger.warning("No transcription result")
                return
            
            logger.info(f"Transcribed: {text}")
            
            # Check for stop command first (before any other processing)
            text_lower = text.lower().strip()
            stop_keywords = get_stop_words()
            
            # Check for stop keywords more aggressively
            is_stop_command = any(keyword in text_lower for keyword in stop_keywords)
            
            if is_stop_command:
                await self._handle_stop_command()
                return
            
            # First, repeat the command back to confirm understanding
            confirmation = f"I heard: {text}. Let me help you with that."
            logger.info(f"Confirming command: {confirmation}")
            # Run TTS in executor to avoid blocking async event loop
            # But also continue listening for stop commands in parallel
            loop = asyncio.get_event_loop()
            
            # Start TTS in background (non-blocking)
            tts_task = loop.run_in_executor(None, self.tts_engine.speak, confirmation)
            
            # Wait for TTS to complete (background listener will handle stop detection)
            try:
                await tts_task
            except Exception as e:
                logger.warning(f"TTS task interrupted: {e}")
                if not self._listening:
                    return
            
            # Brief pause after confirmation
            await asyncio.sleep(0.3)
            
            # Try command handler first (for weather, time, etc.)
            command_handler = get_command_handler()
            command_response = await command_handler.process(text)
            
            if command_response.handled:
                # Command was handled by a command handler (e.g., weather with auto-location)
                content = command_response.response
                logger.info(f"Command handled by {command_response.command_type}, response (length: {len(content)} chars): {content}")
            else:
                # Fall back to LLM for complex queries
                response = await self.llm_router.generate(
                    prompt=text,
                    system_prompt="You are a helpful personal assistant. Be concise and actionable."
                )
                content = response.get("content", "")
                logger.info(f"LLM response (length: {len(content)} chars): {content}")
            
            # Don't include mode/engine info in spoken response - just speak the content
            # Run TTS in executor to avoid blocking async event loop
            # Background listener will handle stop detection during TTS
            loop = asyncio.get_event_loop()
            
            # Start TTS in background (non-blocking)
            tts_task = loop.run_in_executor(None, self.tts_engine.speak, content)
            
            # Wait for TTS to complete (background listener will handle stop detection)
            try:
                await tts_task
            except Exception as e:
                logger.warning(f"TTS task interrupted: {e}")
                if not self._listening:
                    return
            
            # Call callback if provided
            if self.callback:
                await self.callback(text, content, response)
        
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}", exc_info=True)
            # Run TTS in executor to avoid blocking async event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.tts_engine.speak, "I'm sorry, I encountered an error processing your request.")
    
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
        
        # Start background task to listen for stop commands during TTS
        self._stop_listener_task = asyncio.create_task(self._listen_for_stop_during_tts())
        
        # Simple wake word detection loop
        # In production, you'd use Porcupine's detection
        while self._listening:
            # Check if we should stop before processing
            if not self._listening:
                logger.info("Voice listener stopping (flag set)")
                break
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
        logger.info("Stopping voice listener...")
        self._listening = False
        
        # Cancel background stop listener task
        if self._stop_listener_task and not self._stop_listener_task.done():
            self._stop_listener_task.cancel()
            logger.debug("Cancelled background stop listener task")
        
        try:
            if self.audio_stream:
                logger.debug("Stopping audio stream...")
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
        except Exception as e:
            logger.warning(f"Error stopping audio stream: {e}")
        
        try:
            if self.pyaudio_instance:
                logger.debug("Terminating PyAudio...")
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
        except Exception as e:
            logger.warning(f"Error terminating PyAudio: {e}")
        
        try:
            if self.porcupine:
                logger.debug("Deleting Porcupine...")
                self.porcupine.delete()
                self.porcupine = None
        except Exception as e:
            logger.warning(f"Error deleting Porcupine: {e}")
        
        logger.info("Voice listener stopped successfully")


# Global listener instance
_listener: Optional[VoiceListener] = None


def reset_voice_listener():
    """
    Reset the global voice listener instance to force reload from .env.
    Useful when .env file is updated.
    """
    global _listener
    _listener = None
    logger.info("Voice listener instance reset - will reload on next access")


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
        # Force reload .env file to pick up latest changes
        load_dotenv(override=True)
        
        wake_word = os.getenv("WAKE_WORD", "hey assistant")
        logger.info(f"Initializing voice listener with wake word: '{wake_word}'")
        
        _listener = VoiceListener(
            wake_word=wake_word,
            porcupine_access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
            sensitivity=0.5
        )
    return _listener

