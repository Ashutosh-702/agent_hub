"""Deepgram streaming transcription service."""

import asyncio
import json
import logging
from typing import Callable, Optional, Any, List, Dict
from datetime import datetime

try:
    from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    DeepgramClient = None
    LiveTranscriptionEvents = None
    LiveOptions = None

from config.loaded_config import loaded_config

logger = logging.getLogger(__name__)


class DeepgramTranscriptionService:
    """
    Service for real-time audio transcription using Deepgram.
    
    Handles:
    - Connection to Deepgram streaming API
    - Audio chunk forwarding
    - Transcript callback management
    - Connection lifecycle
    """
    
    def __init__(
        self,
        on_transcript_interim: Optional[Callable[[str, float], None]] = None,
        on_transcript_final: Optional[Callable[[str, str, float], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the Deepgram transcription service.
        
        Args:
            on_transcript_interim: Callback for interim transcripts (text, timestamp) or (text, timestamp, speaker)
            on_transcript_final: Callback for final transcripts (text, speaker, timestamp)
            on_error: Callback for errors (message)
        """
        self.on_transcript_interim = on_transcript_interim
        self.on_transcript_final = on_transcript_final
        self.on_error = on_error
        
        self._client: Optional[Any] = None
        self._connection: Optional[Any] = None
        self._is_connected = False
        self._start_time: Optional[datetime] = None
        
        # Get API key from config
        self._api_key = getattr(loaded_config, 'deepgram_api_key', None)
        
    @property
    def is_connected(self) -> bool:
        """Check if connected to Deepgram."""
        return self._is_connected
    
    async def connect(self) -> bool:
        """
        Establish connection to Deepgram streaming API.
        
        Returns:
            True if connection successful, False otherwise.
        """
        if not DEEPGRAM_AVAILABLE:
            logger.error("Deepgram SDK not installed. Run: pip install deepgram-sdk")
            if self.on_error:
                self.on_error("Deepgram SDK not available")
            return False
        
        if not self._api_key:
            logger.error("Deepgram API key not configured")
            if self.on_error:
                self.on_error("Deepgram API key not configured")
            return False
        
        try:
            logger.info("Initializing Deepgram client...")
            # Initialize Deepgram client
            self._client = DeepgramClient(self._api_key)
            logger.info("Deepgram client created")
            
            # Create live transcription connection
            # According to Deepgram SDK docs: client.listen.live.v("1") for streaming
            logger.info("Creating Deepgram live connection...")
            self._connection = self._client.listen.live.v("1")
            logger.info("Deepgram live connection object created")
            
            # Set up event handlers
            logger.info("Setting up Deepgram event handlers...")
            self._connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self._connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self._connection.on(LiveTranscriptionEvents.Error, self._on_deepgram_error)
            self._connection.on(LiveTranscriptionEvents.Close, self._on_close)
            logger.info("Event handlers registered")
            
            # Configure transcription options
            logger.info("Configuring Deepgram options...")
            # Explicitly set channels=1 for mono audio
            # linear16 encoding requires little-endian byte order (default in JavaScript/Python)
            # Support multiple languages using language="multi" parameter
            # According to Deepgram docs: https://developers.deepgram.com/docs/multilingual-code-switching
            # Use language="multi" with nova-2 or nova-3 model for automatic language detection
            # This enables transcription in Hindi, English, and 30+ other languages automatically
            # Nova-2 supports 20+ languages including Hindi, English, Spanish, French, etc.
            # Nova-3 Multilingual supports real-time code-switching across 10 languages
            options = LiveOptions(
                model="nova-3",  # Use nova-3 model (latest model with enhanced multilingual support)
                language="multi",  # Multilingual mode - automatically detects and transcribes in multiple languages
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
                endpointing=300,
                multichannel=True,  # Process each channel separately (Channel 0 = Mic, Channel 1 = System Audio)
                diarize=False,  # Disable diarization when using multichannel - each channel is already a separate source
                punctuate=True,
                encoding="linear16",
                sample_rate=16000,
                channels=2,  # Stereo: Channel 0 = Microphone (user), Channel 1 = System Audio (client)
            )
            logger.info(f"Options configured: model={options.model}, language={options.language} (multilingual - auto-detects Hindi, English, and 30+ languages), encoding={options.encoding}, sample_rate={options.sample_rate}, channels={options.channels} ({'stereo' if options.channels == 2 else 'mono'}), multichannel={getattr(options, 'multichannel', False)}, diarize={getattr(options, 'diarize', False)}")
            
            # Start the connection (start() is synchronous, returns bool)
            logger.info("Starting Deepgram connection...")
            start_result = self._connection.start(options)
            logger.info(f"Deepgram start() returned: {start_result}")
            
            if start_result:
                self._start_time = datetime.utcnow()
                logger.info("Waiting for Deepgram Open event...")
                # Wait briefly for Open event to fire (set by _on_open callback)
                # This ensures Deepgram has fully established the connection
                await asyncio.sleep(0.5)  # Increased wait time
                # is_connected will be set by _on_open callback
                if self._is_connected:
                    logger.info("✅ Connected to Deepgram streaming API successfully!")
                    return True
                else:
                    logger.warning("⚠️ Deepgram start() succeeded but Open event not yet received - connection may still be establishing")
                    # Still return True as connection might be establishing
                    return True
            else:
                logger.error("❌ Failed to start Deepgram connection - start() returned False")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error connecting to Deepgram: {e}", exc_info=True)
            if self.on_error:
                self.on_error(f"Connection error: {str(e)}")
            return False
    
    def _on_open(self, *args, **kwargs):
        """Handle connection open event."""
        logger.info("🎉 Deepgram Open event received!")
        self._is_connected = True
        logger.info("✅ Deepgram connection opened and marked as connected")
    
    def _on_transcript(self, *args, **kwargs):
        """Handle transcript event from Deepgram."""
        logger.info("📝 Deepgram Transcript event received!")
        logger.info(f"📋 Args count: {len(args)}, Kwargs keys: {list(kwargs.keys())}")
        
        try:
            # Extract result from kwargs or args
            # Deepgram SDK v3 passes result as first positional arg or in kwargs
            result = kwargs.get('result') or (args[0] if len(args) > 0 else None)
            
            if not result:
                logger.warning("⚠️ Transcript event received but result is None")
                logger.warning(f"   Args: {args}, Kwargs: {kwargs}")
                return
            
            logger.info(f"📋 Result type: {type(result)}")
            logger.info(f"📋 Result attributes: {dir(result)}")
            
            # Try to get is_final
            is_final = getattr(result, 'is_final', None)
            logger.info(f"📋 is_final: {is_final}")
            
            # Get the transcript - try different ways
            transcript = None
            channel = None
            
            # Method 1: result.channel.alternatives[0].transcript
            try:
                channel = result.channel
                logger.info(f"📋 Channel: {channel}")
                alternatives = channel.alternatives if hasattr(channel, 'alternatives') else None
                logger.info(f"📋 Alternatives: {alternatives}")
                
                if alternatives and len(alternatives) > 0:
                    transcript = alternatives[0].transcript if hasattr(alternatives[0], 'transcript') else None
                    logger.info(f"📋 Transcript from alternatives: {transcript}")
            except Exception as e1:
                logger.warning(f"⚠️ Method 1 failed: {e1}")
            
            # Method 2: result.sentence (some Deepgram versions use this)
            if not transcript:
                try:
                    if hasattr(result, 'sentence'):
                        transcript = result.sentence
                        logger.info(f"📋 Transcript from sentence: {transcript}")
                except Exception as e2:
                    logger.warning(f"⚠️ Method 2 failed: {e2}")
            
            # Method 3: Direct transcript attribute
            if not transcript:
                try:
                    if hasattr(result, 'transcript'):
                        transcript = result.transcript
                        logger.info(f"📋 Transcript from direct attribute: {transcript}")
                except Exception as e3:
                    logger.warning(f"⚠️ Method 3 failed: {e3}")
            
            if not transcript:
                logger.warning("⚠️ Could not extract transcript from result")
                logger.warning(f"   Result structure: {result}")
                return
            
            # Handle empty transcripts - these are normal for interim results or silence
            transcript_text = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
            if not transcript_text:
                logger.debug(f"Empty transcript received (is_final={is_final}, speech_final={getattr(result, 'speech_final', False)}) - this is normal for silence or interim results")
                return
            
            # We have a non-empty transcript!
            logger.info(f"🎯 NON-EMPTY transcript extracted: '{transcript_text[:100]}...'")
            
            # Use the cleaned transcript text
            transcript = transcript_text
            
            # Calculate timestamp from start
            timestamp = 0.0
            if self._start_time:
                timestamp = (datetime.utcnow() - self._start_time).total_seconds()
            
            # Check if this is a final result
            is_final = getattr(result, 'is_final', False)
            speech_final = getattr(result, 'speech_final', False)
            logger.info(f"📋 is_final: {is_final}, speech_final: {speech_final}")
            
            # Get speaker based on channel_index (for stereo audio)
            # Channel 0 = Microphone (user), Channel 1 = System Audio (client)
            # If channel_index is not available, fall back to diarization
            speaker = "user"  # Default to user (microphone)
            try:
                # First, try to get channel_index from result (for multi-channel audio)
                # According to Deepgram docs: https://developers.deepgram.com/docs/multichannel
                # For streaming with multichannel=true, channel_index is [channel_number, total_channels]
                # e.g., [0, 2] = channel 0 of 2 channels, [1, 2] = channel 1 of 2 channels
                channel_index = None
                if hasattr(result, 'channel_index') and result.channel_index:
                    if isinstance(result.channel_index, list):
                        # For multichannel streaming, channel_index is [channel_number, total_channels]
                        # Extract the first element as the channel number
                        if len(result.channel_index) >= 1:
                            channel_index = result.channel_index[0]
                            total_channels = result.channel_index[1] if len(result.channel_index) > 1 else None
                            logger.info(f"📋 Channel index from result: {channel_index} (of {total_channels} total channels)")
                        else:
                            channel_index = None
                    else:
                        # Single integer value (shouldn't happen with multichannel, but handle it)
                        channel_index = result.channel_index
                        logger.info(f"📋 Channel index from result: {channel_index} (single value)")
                
                # Map channel_index to speaker labels
                # Channel 0 = Microphone = "user"
                # Channel 1 = System Audio = "client"
                if channel_index is not None:
                    if channel_index == 0:
                        speaker = "user"  # Microphone (left channel)
                    elif channel_index == 1:
                        speaker = "client"  # System audio (right channel)
                    else:
                        # Fallback for other channels
                        speaker = "client"
                    logger.info(f"📋 Speaker from channel_index: channel_{channel_index} → {speaker}")
                else:
                    # Use diarization to identify speakers when channel_index is not reliable
                    # When channel_index is an array with multiple values, we can't determine the source channel
                    # So we rely on diarization to identify speakers by voice characteristics
                    speaker_id = None
                    # Try to get alternatives from channel if we have it
                    if channel and hasattr(channel, 'alternatives') and channel.alternatives:
                        alt = channel.alternatives[0]
                        words = getattr(alt, 'words', None) if hasattr(alt, 'words') else None
                        if words and len(words) > 0:
                            first_word = words[0]
                            if hasattr(first_word, 'speaker'):
                                speaker_id = first_word.speaker
                                logger.info(f"📋 Speaker ID from channel.alternatives[0].words[0]: {speaker_id}")
                    # Also try to get from result directly
                    if speaker_id is None and hasattr(result, 'words') and result.words:
                        first_word = result.words[0]
                        if hasattr(first_word, 'speaker'):
                            speaker_id = first_word.speaker
                            logger.info(f"📋 Speaker ID from result.words[0]: {speaker_id}")
                    
                    # Map speaker ID to our labels
                    # speaker_0 = user (microphone), speaker_1 = client (system audio)
                    if speaker_id is not None:
                        if speaker_id == 0:
                            speaker = "user"  # Microphone = user
                        elif speaker_id == 1:
                            speaker = "client"  # System audio = client
                        else:
                            # For additional speakers, default to client
                            speaker = "client"
                        logger.info(f"📋 Speaker from diarization: speaker_{speaker_id} → {speaker}")
                    else:
                        logger.warning(f"⚠️ Could not extract speaker_id from result - defaulting to 'user'")
                        speaker = "user"  # Default fallback
            except Exception as e:
                logger.debug(f"Could not extract speaker info: {e}")
            
            if is_final or speech_final:
                logger.info(f"✅ FINAL transcript: '{transcript[:100]}...' (speaker: {speaker}, timestamp: {timestamp:.2f}s)")
                if self.on_transcript_final:
                    logger.info("📞 Calling on_transcript_final callback...")
                    try:
                        self.on_transcript_final(transcript, speaker, timestamp)
                        logger.info("✅ on_transcript_final callback completed successfully")
                    except Exception as callback_error:
                        logger.error(f"❌ Error in on_transcript_final callback: {callback_error}", exc_info=True)
                else:
                    logger.error("❌ on_transcript_final callback is None!")
            else:
                logger.info(f"🔄 INTERIM transcript: '{transcript[:50]}...' (speaker: {speaker}, timestamp: {timestamp:.2f}s)")
                if self.on_transcript_interim:
                    logger.debug("📞 Calling on_transcript_interim callback...")
                    try:
                        # Pass speaker to interim callback if it accepts 3 args, otherwise use 2 args for backward compatibility
                        import inspect
                        sig = inspect.signature(self.on_transcript_interim)
                        if len(sig.parameters) >= 3:
                            self.on_transcript_interim(transcript, timestamp, speaker)
                        else:
                            self.on_transcript_interim(transcript, timestamp)
                        logger.debug("✅ on_transcript_interim callback completed")
                    except Exception as callback_error:
                        logger.error(f"❌ Error in on_transcript_interim callback: {callback_error}", exc_info=True)
                else:
                    logger.warning("⚠️ on_transcript_interim callback is None!")
                    
        except Exception as e:
            logger.error(f"❌ Error processing transcript: {e}", exc_info=True)
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
    
    def _on_deepgram_error(self, *args, **kwargs):
        """Handle error event from Deepgram."""
        error = kwargs.get('error') or (args[1] if len(args) > 1 else "Unknown error")
        logger.error(f"Deepgram error: {error}")
        if self.on_error:
            self.on_error(str(error))
    
    def _on_close(self, *args, **kwargs):
        """Handle connection close event."""
        self._is_connected = False
        logger.info("Deepgram connection closed")
    
    async def send_audio(self, audio_data: bytes) -> bool:
        """
        Send audio chunk to Deepgram for transcription.
        
        Args:
            audio_data: Raw audio bytes (PCM 16-bit, 16kHz, mono recommended)
            
        Returns:
            True if sent successfully, False otherwise.
        """
        if not self._is_connected:
            logger.debug(f"⚠️ Cannot send audio: not connected (is_connected={self._is_connected})")
            return False
        
        if not self._connection:
            logger.warning(f"⚠️ Cannot send audio: connection object is None")
            return False
        
        try:
            # Calculate audio level for debugging (RMS from Int16 PCM)
            if len(audio_data) >= 2:
                # Convert bytes to Int16 samples (little-endian)
                int16_samples = []
                for i in range(0, len(audio_data) - 1, 2):
                    # Little-endian: low byte first, then high byte
                    sample = int.from_bytes(audio_data[i:i+2], byteorder='little', signed=True)
                    int16_samples.append(sample)
                
                if int16_samples:
                    # Calculate RMS
                    sum_squares = sum(s * s for s in int16_samples)
                    rms = (sum_squares / len(int16_samples)) ** 0.5
                    # Normalize to 0-1 range (Int16 max is 32767)
                    normalized_rms = rms / 32767.0
                    db = 20 * (sum_squares / len(int16_samples)) ** 0.5 if sum_squares > 0 else -100
                    
                    # Log audio level occasionally
                    # Log audio level occasionally to verify audio is being captured
                    if len(int16_samples) > 0:
                        max_abs = max(abs(s) for s in int16_samples[:min(10, len(int16_samples))])
                        # Log every ~50 chunks (2% chance)
                        import random
                        if random.random() < 0.02:
                            # Calculate expected sample rate from chunk size (960 bytes = 480 Int16 samples = 30ms at 16kHz)
                            expected_samples_16khz = len(audio_data) // 2  # 2 bytes per Int16 sample
                            logger.info(f"📊 Audio level: RMS={normalized_rms:.4f}, dB={db:.2f}, samples={len(int16_samples)}, max_abs={max_abs}, chunk_size={len(audio_data)} bytes, expected_samples_16khz={expected_samples_16khz}, has_audio={'YES' if normalized_rms > 0.001 else 'NO (silence)'}")
            
            logger.debug(f"📤 Sending audio chunk: {len(audio_data)} bytes to Deepgram...")
            self._connection.send(audio_data)
            logger.debug(f"✅ Successfully sent {len(audio_data)} bytes to Deepgram")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending audio to Deepgram: {e}", exc_info=True)
            if self.on_error:
                self.on_error(f"Send error: {str(e)}")
            return False
    
    def send_keepalive(self) -> bool:
        """
        Send keepalive message to Deepgram to prevent timeout.
        
        Deepgram requires either:
        1. keep_alive() method call (text keepalive)
        2. OR regular audio data (silence works)
        
        Returns:
            True if sent successfully, False otherwise.
        """
        if not self._is_connected or not self._connection:
            return False
        
        try:
            # Try Deepgram's built-in keep_alive method first
            if hasattr(self._connection, 'keep_alive') and callable(self._connection.keep_alive):
                result = self._connection.keep_alive()
                if result:
                    logger.debug("Sent Deepgram keepalive (text)")
                    return True
                else:
                    logger.warning("keep_alive() returned False, falling back to silence audio")
            
            # Fallback: Send silence audio chunk (160 bytes = 10ms of silence at 16kHz, 16-bit mono)
            # This ensures Deepgram receives data and doesn't timeout
            silence_chunk = b'\x00\x00' * 80  # 160 bytes of silence
            self._connection.send(silence_chunk)
            logger.debug("Sent Deepgram keepalive (silence audio)")
            return True
        except Exception as e:
            logger.error(f"Error sending keepalive to Deepgram: {e}")
            return False
    
    async def close(self):
        """Close the Deepgram connection."""
        if self._connection:
            try:
                # finish() is synchronous, returns bool
                self._connection.finish()
                logger.info("Deepgram connection finished")
            except Exception as e:
                logger.error(f"Error closing Deepgram connection: {e}")
        
        self._is_connected = False
        self._connection = None
        self._client = None
        self._start_time = None


class MockDeepgramService:
    """
    Mock Deepgram service for development/testing without actual Deepgram API.
    Simulates transcription by echoing received audio info.
    """
    
    def __init__(
        self,
        on_transcript_interim: Optional[Callable[[str, float], None]] = None,
        on_transcript_final: Optional[Callable[[str, str, float], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.on_transcript_interim = on_transcript_interim
        self.on_transcript_final = on_transcript_final
        self.on_error = on_error
        self._is_connected = False
        self._start_time: Optional[datetime] = None
        self._transcript_count = 0
        
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    async def connect(self) -> bool:
        """Simulate connection."""
        self._is_connected = True
        self._start_time = datetime.utcnow()
        logger.info("Mock Deepgram service connected")
        return True
    
    async def send_audio(self, audio_data: bytes) -> bool:
        """Simulate processing audio and generating transcripts."""
        if not self._is_connected:
            return False
        
        self._transcript_count += 1
        timestamp = (datetime.utcnow() - self._start_time).total_seconds() if self._start_time else 0.0
        
        # Simulate interim transcript every few chunks
        if self._transcript_count % 3 == 0 and self.on_transcript_interim:
            self.on_transcript_interim(f"[Mock interim transcript {self._transcript_count}...]", timestamp)
        
        # Simulate final transcript every 5 chunks
        if self._transcript_count % 5 == 0 and self.on_transcript_final:
            self.on_transcript_final(
                f"This is mock transcript segment {self._transcript_count // 5}.",
                "user",
                timestamp
            )
        
        return True
    
    def send_keepalive(self) -> bool:
        """Mock keepalive - just return True if connected."""
        if not self._is_connected:
            return False
        # Mock service doesn't need actual keepalive, just return success
        return True
    
    async def close(self):
        """Simulate closing connection."""
        self._is_connected = False
        self._start_time = None
        self._transcript_count = 0
        logger.info("Mock Deepgram service closed")


def create_transcription_service(
    on_transcript_interim: Optional[Callable[[str, float], None]] = None,
    on_transcript_final: Optional[Callable[[str, str, float], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    use_mock: bool = False,
) -> DeepgramTranscriptionService:
    """
    Factory function to create the appropriate transcription service.
    
    Args:
        on_transcript_interim: Callback for interim transcripts
        on_transcript_final: Callback for final transcripts
        on_error: Callback for errors
        use_mock: If True, use mock service instead of real Deepgram
        
    Returns:
        Transcription service instance
    """
    if use_mock or not DEEPGRAM_AVAILABLE:
        logger.info("Using mock transcription service")
        return MockDeepgramService(
            on_transcript_interim=on_transcript_interim,
            on_transcript_final=on_transcript_final,
            on_error=on_error,
        )
    
    return DeepgramTranscriptionService(
        on_transcript_interim=on_transcript_interim,
        on_transcript_final=on_transcript_final,
        on_error=on_error,
    )


async def transcribe_prerecorded_audio(
    audio_data: bytes,
    filename: str,
) -> List[Dict[str, Any]]:
    """
    Transcribe a prerecorded audio file using Deepgram.
    
    Args:
        audio_data: Audio file bytes
        filename: Original filename (for format detection)
        
    Returns:
        List of transcript entries with format:
        [
            {
                "timestamp": float,
                "speaker": str,
                "text": str,
                "is_final": bool
            },
            ...
        ]
    """
    import asyncio
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
    
    if not DEEPGRAM_AVAILABLE:
        logger.error("Deepgram SDK not installed")
        raise RuntimeError("Deepgram SDK not available")
    
    api_key = getattr(loaded_config, 'deepgram_api_key', None)
    if not api_key:
        logger.error("Deepgram API key not configured")
        raise RuntimeError("Deepgram API key not configured")
    
    try:
        logger.info(f"Transcribing prerecorded audio file: {filename} ({len(audio_data)} bytes)")
        
        # Initialize Deepgram client
        client = DeepgramClient(api_key)
        
        # Create file source from bytes
        payload: FileSource = {
            "buffer": audio_data,
        }
        
        # Configure transcription options
        options = PrerecordedOptions(
            model="nova-3",
            language="multi",  # Multilingual support
            smart_format=True,
            punctuate=True,
            diarize=True,  # Enable speaker diarization
        )
        
        # Transcribe (using synchronous API for prerecorded)
        response = client.listen.rest.v("1").transcribe_file(payload, options)
        
        # Parse response and convert to transcript entries
        transcript_entries = []
        
        # Deepgram SDK v3 returns response object with results attribute
        if hasattr(response, 'results'):
            results = response.results
            if results and hasattr(results, 'channels'):
                channels = results.channels
                if channels and len(channels) > 0:
                    channel = channels[0]
                    if hasattr(channel, 'alternatives') and channel.alternatives:
                        alternative = channel.alternatives[0]
                        transcript_text = getattr(alternative, 'transcript', '')
                        words = getattr(alternative, 'words', [])
                        
                        # Group words by speaker and create entries
                        current_speaker = None
                        current_text = []
                        current_start = None
                        
                        for word in words:
                            word_text = getattr(word, 'word', '')
                            word_speaker = getattr(word, 'speaker', 0)
                            word_start = getattr(word, 'start', 0)
                            
                            # Map speaker ID to label
                            speaker_label = "user" if word_speaker == 0 else "client"
                            
                            if current_speaker is None:
                                current_speaker = speaker_label
                                current_start = word_start
                            
                            if speaker_label != current_speaker:
                                # Speaker changed, save previous entry
                                if current_text:
                                    transcript_entries.append({
                                        "timestamp": current_start or 0.0,
                                        "speaker": current_speaker,
                                        "text": " ".join(current_text),
                                        "is_final": True,
                                    })
                                
                                # Start new entry
                                current_speaker = speaker_label
                                current_start = word_start
                                current_text = [word_text]
                            else:
                                current_text.append(word_text)
                        
                        # Add final entry
                        if current_text:
                            transcript_entries.append({
                                "timestamp": current_start or 0.0,
                                "speaker": current_speaker or "user",
                                "text": " ".join(current_text),
                                "is_final": True,
                            })
        
        # Fallback: If no structured entries, create single entry from full transcript
        if not transcript_entries and hasattr(response, 'results'):
            results = response.results
            if results and hasattr(results, 'channels'):
                channels = results.channels
                if channels and len(channels) > 0:
                    channel = channels[0]
                    if hasattr(channel, 'alternatives') and channel.alternatives:
                        alternative = channel.alternatives[0]
                        transcript_text = getattr(alternative, 'transcript', '')
                        if transcript_text:
                            transcript_entries.append({
                                "timestamp": 0.0,
                                "speaker": "user",
                                "text": transcript_text,
                                "is_final": True,
                            })
        
        logger.info(f"Transcription complete: {len(transcript_entries)} entries")
        return transcript_entries
        
    except Exception as e:
        logger.error(f"Error transcribing audio file: {e}", exc_info=True)
        raise RuntimeError(f"Failed to transcribe audio: {str(e)}")

