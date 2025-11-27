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
        "quit",
        "bye",
        "goodbye",
        "see you later"
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
        self._continuous_mode = False  # After first command, continue listening without wake word
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
        logger.info("🛑 Stop command detected - shutting down voice listener")
        
        # Set listening flag to False FIRST to stop all loops immediately
        self._listening = False
        logger.info("Set _listening flag to False")
        
        # Stop any ongoing TTS immediately (this is critical)
        try:
            logger.info("Attempting to stop ongoing TTS...")
            self.tts_engine.stop_speaking()
            logger.info("✅ Stopped ongoing TTS")
        except Exception as e:
            logger.warning(f"Error stopping TTS: {e}", exc_info=True)
        
        # Small delay to ensure TTS actually stops
        await asyncio.sleep(0.2)
        
        # Get user name from environment or use default
        user_name = os.getenv("USER_NAME", "Himanshu")
        goodbye_message = f"Goodbye {user_name}"
        
        # Try to speak goodbye message (but don't wait too long)
        try:
            loop = asyncio.get_event_loop()
            logger.info(f"Speaking goodbye message: {goodbye_message}")
            # Use asyncio.wait_for to prevent hanging
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self.tts_engine.speak, goodbye_message, True),
                timeout=3.0
            )
            if result:
                logger.info("Goodbye message spoken successfully")
        except asyncio.TimeoutError:
            logger.warning("Goodbye message timed out - proceeding with shutdown")
        except Exception as e:
            logger.warning(f"Error speaking goodbye: {e}")
        
        # Stop the listener and clean up resources
        logger.info("Calling stop() method to clean up resources...")
        self.stop()
        logger.info("✅ Voice listener stop() completed - exiting")
    
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
                            import string
                            text_lower = text.lower().strip()
                            text_clean = text_lower.translate(str.maketrans('', '', string.punctuation))
                            stop_keywords = get_stop_words()
                            
                            # Check if any stop keyword is in the transcribed text
                            # Check multiple ways: contains, starts with, ends with (with and without punctuation)
                            is_stop = any(
                                keyword in text_lower or 
                                keyword in text_clean or
                                text_lower.startswith(keyword) or 
                                text_lower.endswith(keyword) or
                                text_clean.startswith(keyword) or
                                text_clean.endswith(keyword)
                                for keyword in stop_keywords
                            )
                            
                            if is_stop:
                                matched_keywords = [kw for kw in stop_keywords if kw in text_lower]
                                logger.info(f"🛑 Stop command detected during TTS: '{text}' (matched: {matched_keywords})")
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
    
    async def _record_and_process_command(self, require_wake_word: bool = True):
        """
        Record a voice command and process it.
        
        Args:
            require_wake_word: If True, wait for wake word first. If False, start recording immediately.
        """
        if require_wake_word:
            # Wait for wake word first (handled by main loop)
            return
        
        # Start recording immediately (continuous mode - no wake word needed)
        logger.info("Recording next command (continuous mode - no wake word needed)...")
        
        # Brief pause for audio system to settle
        await asyncio.sleep(0.3)
        
        # Record command with Voice Activity Detection
        audio_frames = []
        silence_frames = 0
        max_silence_frames = 90  # ~3 seconds of silence before stopping (increased for natural pauses)
        speech_detected = False
        max_recording_frames = 300  # ~10 seconds max (increased for longer commands)
        energy_threshold = 400  # Lowered to catch quieter speech
        
        # Skip initial frames to avoid any echo
        skip_initial_frames = 5  # Reduced since no TTS just happened
        for i in range(skip_initial_frames):
            try:
                frame = self.audio_stream.read(512, exception_on_overflow=False)
                await asyncio.sleep(0.032)
            except Exception as e:
                logger.warning(f"Error skipping initial frame {i}: {e}")
                break
        
        # Record with VAD - improved to handle natural pauses in speech
        logger.debug(f"Starting continuous mode VAD: max_frames={max_recording_frames}, energy_threshold={energy_threshold}, max_silence={max_silence_frames}")
        for i in range(max_recording_frames):
            try:
                frame = self.audio_stream.read(512, exception_on_overflow=False)
                
                if len(frame) >= 2:
                    samples = struct.unpack(f'{len(frame)//2}h', frame)
                    energy = sum(abs(s) for s in samples) / len(samples) if samples else 0
                    
                    if energy > energy_threshold:
                        if not speech_detected:
                            logger.info(f"Speech detected at frame {i} (energy={energy:.0f})")
                        speech_detected = True
                        silence_frames = 0
                        audio_frames.append(frame)
                    elif speech_detected:
                        # Speech was detected, now we're in a pause
                        # Continue recording during brief pauses (natural in speech)
                        audio_frames.append(frame)  # Always record during pauses after speech
                        silence_frames += 1
                        if silence_frames >= max_silence_frames:
                            logger.info(f"Extended silence detected after speech ({silence_frames} frames), stopping recording (frame {i}, total frames: {len(audio_frames)})")
                            break
                    else:
                        # No speech detected yet - wait for user to start speaking
                        # Record initial frames to catch the start of speech
                        silence_frames += 1
                        if silence_frames < 30:  # Wait up to ~1 second for speech to start
                            audio_frames.append(frame)
                        # If too much silence at start without speech, might be background noise
                
                await asyncio.sleep(0.032)
            except Exception as e:
                logger.error(f"Error reading audio frame {i}: {e}", exc_info=True)
                break
        
        if not audio_frames:
            logger.warning("No audio frames recorded in continuous mode")
            return
        
        audio_data = b''.join(audio_frames)
        duration_seconds = len(audio_data) / (self.sample_rate * self.channels * self.sample_width)
        logger.info(f"Recorded {len(audio_frames)} frames ({duration_seconds:.2f}s) in continuous mode")
        
        if duration_seconds < 0.1:
            logger.warning(f"Audio too short ({duration_seconds:.2f}s)")
            return
        
        await self._process_voice_command(audio_data)
    
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
                logger.warning("⚠️ No transcription result - audio may be too short or unclear")
                # Try to give user feedback
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.tts_engine.speak, "I didn't catch that. Could you repeat?")
                return
            
            text = text.strip()
            if len(text) < 3:
                logger.warning(f"⚠️ Transcription too short: '{text}' - may be incomplete")
            
            logger.info(f"✅ Transcribed ({len(text)} chars): '{text}'")
            
            # Check for stop command first (before any other processing)
            # Strip punctuation for better matching
            import string
            text_lower = text.lower().strip()
            text_clean = text_lower.translate(str.maketrans('', '', string.punctuation))
            stop_keywords = get_stop_words()
            
            # Check for stop keywords more aggressively
            # Check both with and without punctuation
            is_stop_command = any(
                keyword in text_lower or 
                keyword in text_clean or
                text_lower.startswith(keyword) or 
                text_lower.endswith(keyword) or
                text_clean.startswith(keyword) or
                text_clean.endswith(keyword)
                for keyword in stop_keywords
            )
            
            if is_stop_command:
                matched_keywords = [kw for kw in stop_keywords if kw in text_lower]
                logger.info(f"🛑 Stop command detected in transcription: '{text}' (matched: {matched_keywords})")
                await self._handle_stop_command()
                return
            
            # First, repeat the command back to confirm understanding
            # Only confirm if transcription seems complete (more than a few words)
            if len(text.split()) > 2:
                confirmation = f"I heard: {text}. Let me help you with that."
            else:
                # If transcription is very short, ask for clarification
                confirmation = f"I heard: {text}. Is that correct?"
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
            logger.info(f"Attempting to process command with command handler: '{text}'")
            command_handler = get_command_handler()
            command_response = await command_handler.process(text)
            
            if command_response.handled:
                # Command was handled by a command handler (e.g., weather with auto-location)
                content = command_response.response
                logger.info(f"✅ Command handled by {command_response.command_type}, response (length: {len(content)} chars): {content}")
            else:
                # Fall back to LLM for complex queries
                logger.info(f"Command not handled by any handler, using LLM: '{text}'")
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
            
            # After processing command, enter continuous listening mode
            # User can give another command without saying wake word again
            if self._listening:
                logger.info("Entering continuous listening mode - ready for next command")
                self._continuous_mode = True
                # Brief pause after response, then start listening for next command
                await asyncio.sleep(1.0)  # Give user time to process response
                # Start recording next command (without wake word)
                # This will loop back to _process_voice_command if another command is detected
                try:
                    await self._record_and_process_command(require_wake_word=False)
                except Exception as e:
                    logger.error(f"Error in continuous mode recording: {e}", exc_info=True)
                    self._continuous_mode = False  # Exit continuous mode on error
        
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}", exc_info=True)
            # Run TTS in executor to avoid blocking async event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.tts_engine.speak, "I'm sorry, I encountered an error processing your request.")
            # Still enter continuous mode after error
            if self._listening:
                self._continuous_mode = True
                await asyncio.sleep(0.5)
                await self._record_and_process_command(require_wake_word=False)
    
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
                        self._continuous_mode = False  # Reset continuous mode when wake word is detected
                        
                        # Speak response and WAIT for it to complete
                        loop = asyncio.get_event_loop()
                        logger.info("Speaking wake word response...")
                        await loop.run_in_executor(None, self.tts_engine.speak, "Yes, how can I help?", True)
                        logger.info("Wake word response completed")
                        
                        # Start recording immediately - we'll use VAD to detect when user actually speaks
                        # This avoids missing the beginning of the user's question
                        logger.info("Starting to record voice command immediately...")
                        
                        # Record command with Voice Activity Detection (simple energy-based)
                        logger.info("Recording voice command (waiting for speech)...")
                        audio_frames = []
                        
                        # Simple VAD: detect when user starts speaking (energy threshold)
                        silence_frames = 0
                        max_silence_frames = 90  # ~3 seconds of silence before stopping (increased for natural pauses)
                        speech_detected = False
                        max_recording_frames = 300  # ~10 seconds max (increased for longer commands)
                        energy_threshold = 400  # Lowered to catch quieter speech
                        
                        # Brief wait for audio system to settle (reduced from 0.8s)
                        logger.debug("Brief pause (0.3s) for audio system to settle...")
                        await asyncio.sleep(0.3)
                        
                        # Skip fewer initial frames - just enough to avoid TTS echo
                        # But start recording immediately so we don't miss user's speech
                        skip_initial_frames = 10  # Skip first ~0.3 seconds (reduced from 20)
                        logger.debug(f"Skipping first {skip_initial_frames} frames to avoid TTS echo...")
                        for i in range(skip_initial_frames):
                            try:
                                frame = self.audio_stream.read(512, exception_on_overflow=False)
                                await asyncio.sleep(0.032)
                            except Exception as e:
                                logger.warning(f"Error skipping initial frame {i}: {e}")
                                break
                        logger.debug("Finished skipping initial frames, starting VAD recording...")
                        
                        # Now record with VAD - improved to handle natural pauses in speech
                        logger.debug(f"Starting VAD loop: max_frames={max_recording_frames}, energy_threshold={energy_threshold}, max_silence={max_silence_frames}")
                        for i in range(max_recording_frames):
                            try:
                                frame = self.audio_stream.read(512, exception_on_overflow=False)
                                
                                # Calculate frame energy (simple VAD)
                                if len(frame) >= 2:
                                    # Convert bytes to samples and calculate RMS energy
                                    samples = struct.unpack(f'{len(frame)//2}h', frame)
                                    energy = sum(abs(s) for s in samples) / len(samples) if samples else 0
                                    
                                    if energy > energy_threshold:
                                        if not speech_detected:
                                            logger.info(f"Speech detected at frame {i} (energy={energy:.0f})")
                                        speech_detected = True
                                        silence_frames = 0
                                        audio_frames.append(frame)
                                    elif speech_detected:
                                        # Speech was detected, now we're in a pause
                                        # Continue recording during brief pauses (natural in speech)
                                        audio_frames.append(frame)  # Always record during pauses after speech
                                        silence_frames += 1
                                        if silence_frames >= max_silence_frames:
                                            logger.info(f"Extended silence detected after speech ({silence_frames} frames), stopping recording (frame {i}, total frames: {len(audio_frames)})")
                                            break
                                    else:
                                        # No speech detected yet - wait for user to start speaking
                                        # Record initial frames to catch the start of speech
                                        silence_frames += 1
                                        if silence_frames < 30:  # Wait up to ~1 second for speech to start
                                            audio_frames.append(frame)
                                        # If too much silence at start without speech, might be background noise
                                
                                await asyncio.sleep(0.032)  # ~31 frames per second
                            except Exception as e:
                                logger.error(f"Error reading audio frame {i}: {e}", exc_info=True)
                                break
                        
                        logger.info(f"VAD loop completed: speech_detected={speech_detected}, frames_recorded={len(audio_frames)}")
                        
                        if not audio_frames:
                            logger.warning("No audio frames recorded")
                            await loop.run_in_executor(None, self.tts_engine.speak, "I didn't hear anything. Could you repeat?", True)
                            continue
                        
                        audio_data = b''.join(audio_frames)
                        logger.info(f"Recorded {len(audio_frames)} frames ({len(audio_data)} bytes) of audio")
                        
                        # Calculate audio duration for logging
                        duration_seconds = len(audio_data) / (self.sample_rate * self.channels * self.sample_width)
                        logger.info(f"Audio duration: {duration_seconds:.2f} seconds")
                        
                        if duration_seconds < 0.1:
                            logger.warning(f"Audio too short ({duration_seconds:.2f}s), may not transcribe well")
                        
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
        
        wake_word = os.getenv("WAKE_WORD", "jarvis")  # Default to "jarvis" instead of "hey assistant"
        logger.info(f"Initializing voice listener with wake word: '{wake_word}'")
        
        _listener = VoiceListener(
            wake_word=wake_word,
            porcupine_access_key=os.getenv("PORCUPINE_ACCESS_KEY"),
            sensitivity=0.5
        )
    return _listener

