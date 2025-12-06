"""
Text-to-Speech (TTS) module.
Uses pyttsx3 for local TTS on macOS, with fallback to macOS 'say' command.
"""

import pyttsx3
import threading
import time
import subprocess
import platform
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
        voice_id: Optional[str] = None,
        prefer_male: bool = True
    ):
        """
        Initialize TTS engine.
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice_id: Specific voice ID (optional, uses system default if None)
            prefer_male: If True, prefer male voices (default: True)
        """
        # Lock to ensure only one TTS call at a time
        self._speak_lock = threading.Lock()
        self._current_speak_process: Optional[subprocess.Popen] = None  # Track current TTS process for interruption
        # Store rate for use with 'say' command
        self.rate = rate
        
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            voices = self.engine.getProperty('voices')
            
            # Set voice if specified
            if voice_id:
                for voice in voices:
                    if voice_id in voice.id:
                        self.engine.setProperty('voice', voice.id)
                        logger.info(f"Using voice: {voice.name}")
                        break
            elif prefer_male:
                # Try to find a male voice
                # Common male voice identifiers on macOS (in order of preference)
                # Prioritize natural-sounding voices first
                male_voice_preferences = [
                    'alex',      # Default male voice on macOS (most natural)
                    'daniel',    # British male (natural)
                    'fred',      # Male voice (natural)
                    'ralph',     # Male voice (natural)
                    'tom',       # Male voice
                    'lee',       # Male voice
                    'junior',    # Male voice
                    'bad',       # Bad News (male, but unusual)
                    'bahh',      # Male voice (unusual)
                    'bells',     # Male voice (unusual)
                    'boing',     # Male voice (unusual)
                    'deranged',  # Male voice (unusual)
                    'hysterical', # Male voice (unusual)
                    'pipe',      # Male voice (unusual)
                    'trinoids',  # Male voice (unusual)
                    'whisper',   # Male voice (unusual)
                    'zarvox'     # Male voice (unusual)
                ]
                
                # Exclude known female voices
                female_exclusions = ['kathy', 'princess', 'victoria', 'samantha', 'karen', 'susan', 'tessa', 'veena', 'alice', 'anna', 'amelie', 'amira', 'alva', 'soumya', 'aman', 'aru']
                
                found_male_voice = False
                for preferred in male_voice_preferences:
                    for voice in voices:
                        voice_id_lower = voice.id.lower()
                        voice_name_lower = voice.name.lower()
                        # Check if it matches preferred male voice and is not a female voice
                        if preferred in voice_id_lower or preferred in voice_name_lower:
                            # Make sure it's not a female voice
                            if not any(female in voice_id_lower or female in voice_name_lower for female in female_exclusions):
                                self.engine.setProperty('voice', voice.id)
                                logger.info(f"Using male voice: {voice.name} (ID: {voice.id})")
                                found_male_voice = True
                                break
                    if found_male_voice:
                        break
                
                if not found_male_voice:
                    # Fallback: Try to find any voice that doesn't match female patterns
                    for voice in voices:
                        voice_id_lower = voice.id.lower()
                        voice_name_lower = voice.name.lower()
                        if not any(female in voice_id_lower or female in voice_name_lower for female in female_exclusions):
                            # Additional check: prefer voices with deeper/male-sounding names
                            if any(male in voice_id_lower or male in voice_name_lower for male in ['alex', 'daniel', 'fred', 'ralph', 'tom']):
                                self.engine.setProperty('voice', voice.id)
                                logger.info(f"Using voice: {voice.name} (ID: {voice.id})")
                                break
            
            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def stop_speaking(self) -> None:
        """
        Stop any ongoing speech immediately.
        """
        logger.info("🛑 stop_speaking() called - interrupting TTS immediately")
        
        # CRITICAL: Stop the process FIRST, even if lock is held
        # This ensures immediate interruption
        if self._current_speak_process:
            try:
                logger.info("Stopping TTS (interrupting 'say' command) - FORCE KILL")
                # Force kill immediately for faster response - use SIGKILL for immediate termination
                try:
                    self._current_speak_process.kill()
                    # Don't wait - just kill and move on
                    try:
                        self._current_speak_process.wait(timeout=0.05)
                    except subprocess.TimeoutExpired:
                        # Process didn't die fast enough, that's okay - we killed it
                        pass
                    logger.info("✅ 'say' command killed")
                except Exception as e:
                    logger.warning(f"Error killing TTS process: {e}")
                    # Try to kill all 'say' processes as fallback
                    try:
                        import subprocess
                        subprocess.run(['pkill', '-9', '-f', 'say'], timeout=0.5, capture_output=True)
                        logger.info("✅ Killed all 'say' processes as fallback")
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Error stopping TTS process: {e}", exc_info=True)
            finally:
                self._current_speak_process = None
        
        # Stop pyttsx3 if running
        if self.engine:
            try:
                logger.info("Stopping pyttsx3 engine...")
                self.engine.stop()
                logger.info("✅ pyttsx3 engine stopped")
            except Exception as e:
                logger.warning(f"Error stopping pyttsx3: {e}")
        
        # Also kill any remaining 'say' processes as a safety measure
        try:
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'say'], capture_output=True, timeout=0.5)
            if result.returncode == 0:
                # There are still 'say' processes running, kill them
                subprocess.run(['pkill', '-9', '-f', 'say'], timeout=0.5, capture_output=True)
                logger.info("✅ Killed remaining 'say' processes")
        except:
            pass
        
        logger.info("✅ stop_speaking() completed")
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Speak the given text.
        Uses a lock to ensure only one TTS call happens at a time.
        
        Args:
            text: Text to speak
            wait: Whether to wait for speech to complete
        
        Returns:
            True if successful, False otherwise
        """
        if not self.engine:
            logger.error("TTS engine not available")
            return False
        
        # Use lock to prevent concurrent TTS calls and ensure completion
        with self._speak_lock:
            try:
                logger.info(f"Speaking (length: {len(text)} chars): {text}")
                
                # Use macOS 'say' command directly (more reliable in background processes)
                if platform.system() == "Darwin":  # macOS
                    try:
                        # Get voice name from engine if available
                        voice_name = None
                        if self.engine:
                            try:
                                voice_id = self.engine.getProperty('voice')
                                # Extract voice name from voice ID (e.g., "com.apple.speech.synthesis.voice.Alex")
                                if voice_id:
                                    voice_parts = voice_id.split('.')
                                    if len(voice_parts) > 0:
                                        voice_name = voice_parts[-1]
                            except:
                                pass
                        
                        # Build say command
                        cmd = ['say']
                        if voice_name:
                            cmd.extend(['-v', voice_name])
                        # Add rate if specified (say uses -r for rate in words per minute)
                        if hasattr(self, 'rate') and self.rate:
                            cmd.extend(['-r', str(self.rate)])
                        cmd.append(text)
                        
                        # Run say command and wait for completion
                        # Use Popen instead of run so we can interrupt it
                        self._current_speak_process = subprocess.Popen(
                            cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        
                        # Wait for completion with timeout, but check periodically if process was killed
                        # Use shorter timeout intervals to allow interruption
                        max_wait_time = 60
                        check_interval = 0.1  # Check every 100ms
                        elapsed = 0
                        
                        try:
                            while elapsed < max_wait_time:
                                try:
                                    # Check if process is still running
                                    result = self._current_speak_process.poll()
                                    if result is not None:
                                        # Process completed
                                        process_result = result
                                        self._current_speak_process = None
                                        
                                        if process_result == 0:
                                            logger.info(f"Finished speaking via 'say' command (length: {len(text)} chars)")
                                            return True
                                        else:
                                            logger.warning(f"'say' command exited with code {process_result} (may have been interrupted)")
                                            return False
                                    
                                    # Process still running, wait a bit
                                    time.sleep(check_interval)
                                    elapsed += check_interval
                                    
                                    # Check if process was killed externally (stop_speaking was called)
                                    if self._current_speak_process is None:
                                        logger.info("TTS process was interrupted by stop_speaking()")
                                        return False
                                        
                                except Exception as poll_error:
                                    logger.warning(f"Error polling process: {poll_error}")
                                    break
                            
                            # Timeout reached
                            logger.error("'say' command timed out")
                            if self._current_speak_process:
                                self._current_speak_process.kill()
                                self._current_speak_process = None
                            # Fallback to pyttsx3
                            return self._speak_pyttsx3(text, wait)
                        except Exception as wait_error:
                            logger.warning(f"Error waiting for TTS process: {wait_error}")
                            if self._current_speak_process:
                                try:
                                    self._current_speak_process.kill()
                                except:
                                    pass
                                self._current_speak_process = None
                            # Fallback to pyttsx3
                            return self._speak_pyttsx3(text, wait)
                    except Exception as say_error:
                        logger.warning(f"'say' command error: {say_error}, trying pyttsx3")
                        if self._current_speak_process:
                            try:
                                self._current_speak_process.kill()
                            except:
                                pass
                            self._current_speak_process = None
                        # Fallback to pyttsx3
                        return self._speak_pyttsx3(text, wait)
                else:
                    # Non-macOS: use pyttsx3
                    return self._speak_pyttsx3(text, wait)
            except Exception as e:
                logger.error(f"TTS failed: {e}", exc_info=True)
                import traceback
                logger.error(f"TTS traceback: {traceback.format_exc()}")
                return False
    
    def _speak_pyttsx3(self, text: str, wait: bool = True) -> bool:
        """Fallback method using pyttsx3."""
        try:
            # Stop any ongoing speech first
            try:
                self.engine.stop()
            except:
                pass
            
            # Use the main engine directly with lock protection
            self.engine.say(text)
            if wait:
                # runAndWait() blocks until speech completes
                self.engine.runAndWait()
                logger.debug(f"TTS runAndWait() completed")
            else:
                self.engine.startLoop(False)
            
            logger.info(f"Finished speaking via pyttsx3 (length: {len(text)} chars)")
            return True
        except Exception as e:
            logger.error(f"pyttsx3 failed: {e}", exc_info=True)
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
        
        # Get voice preference from env (default to female/False)
        prefer_male = os.getenv("TTS_PREFER_MALE", "false").lower() == "true"
        voice_id = os.getenv("TTS_VOICE_ID", None)
        
        _tts_engine = TTSEngine(
            rate=int(os.getenv("TTS_RATE", "150")),
            volume=float(os.getenv("TTS_VOLUME", "0.8")),
            voice_id=voice_id,
            prefer_male=prefer_male
        )
    return _tts_engine
