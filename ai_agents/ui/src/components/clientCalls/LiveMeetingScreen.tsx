import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LiveTranscript } from './LiveTranscript';
import { LiveInsights } from './LiveInsights';
import { MeetingContext } from './MeetingContext';
import { useMeetingWebSocket } from './useMeetingWebSocket';
import { Loader } from '../shared';
import { useGetMeetingByUuidQuery } from '../../store';
import { startSystemAudioCapture, stopSystemAudioCapture, isSystemAudioSupported } from './systemAudioCapture';
import { audioLogger as logger } from '../../utils/logger';

// Mock context for testing
const MOCK_CONTEXT = {
  company: {
    name: 'Acme Retail Ltd',
    industry: 'E-commerce & Retail',
    size: '500-1000 employees',
    website: 'www.acme-retail.com',
  },
  contacts: [
    { name: 'Rajesh Kumar', title: 'VP Operations' },
    { name: 'Priya Sharma', title: 'CTO' },
  ],
  products: ['Fynd OMS', 'Fynd WMS'],
  painPoints: [
    'Inventory visibility across channels',
    'Order fulfillment delays',
    'Manual warehouse processes',
  ],
  previousMeetings: 2,
  dealStage: 'Discovery',
};

export const LiveMeetingScreen = () => {
  const { meetingId } = useParams<{ meetingId: string }>();
  const navigate = useNavigate();
  
  // Fetch meeting data to get call_type
  const { data: meetingResponse, isLoading: meetingLoading } = useGetMeetingByUuidQuery(meetingId || '', {
    skip: !meetingId,
  });
  
  // Debug: Log the meeting response to see what we're getting
  useEffect(() => {
    if (meetingResponse) {
      logger.debug('Full meeting response:', meetingResponse);
      logger.debug('Call type from response:', (meetingResponse.data as any)?.call_type);
    }
  }, [meetingResponse]);
  
  // Try multiple ways to access call_type
  const callType = (
    (meetingResponse?.data as any)?.call_type || 
    (meetingResponse?.data as any)?.callType ||
    undefined
  ) as 'google_meeting' | 'phone_call' | 'in_person' | undefined;
  
  // Log callType whenever it changes
  useEffect(() => {
    logger.debug('callType state:', callType);
  }, [callType]);
  
  const [isPaused, setIsPaused] = useState(false);
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);
  const [pinnedInsights, setPinnedInsights] = useState<Set<string>>(new Set());
  const [actionItems, setActionItems] = useState<string[]>([]);
  const [micError, setMicError] = useState<string | null>(null);
  const [systemAudioError, setSystemAudioError] = useState<string | null>(null);
  
  // Audio capture refs
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const systemAudioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const trackProcessorRef = useRef<ReadableStreamDefaultReader<AudioData> | null>(null);
  const mixerNodeRef = useRef<GainNode | null>(null);
  const micSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const systemSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const isPausedRef = useRef(false);
  const isConnectedRef = useRef(false);
  
  // WebSocket connection
  const {
    isConnected,
    isConnecting,
    isReady, // Deepgram ready state
    transcript,
    insights,
    error,
    connect,
    disconnect,
    sendAudio,
    pauseTranscription,
    resumeTranscription,
  } = useMeetingWebSocket();
  
  // Update refs when state changes
  useEffect(() => {
    isPausedRef.current = isPaused;
  }, [isPaused]);
  
  useEffect(() => {
    isConnectedRef.current = isConnected;
  }, [isConnected]);
  
  // Connect to WebSocket when component mounts
  useEffect(() => {
    if (meetingId) {
      connect(meetingId);
    }
    
    return () => {
      disconnect();
    };
  }, [meetingId, connect, disconnect]);
  
  // Start audio capture when connected AND Deepgram is ready AND meeting data is loaded
  // Note: This effect is placed before startAudioCapture declaration, so we use a ref pattern
  const startAudioCaptureRef = useRef<(() => Promise<void>) | null>(null);
  
  useEffect(() => {
    logger.debug('Audio capture trigger:', {
      isConnected,
      isReady,
      isPaused,
      meetingLoading,
      callType,
    });
    
    // Don't start audio capture until meeting data is loaded (so we know the call type)
    if (meetingLoading) {
      logger.debug('Waiting for meeting data to load...');
      return;
    }
    
    if (isConnected && isReady && !isPaused && startAudioCaptureRef.current) {
      logger.info('Starting audio capture...');
      startAudioCaptureRef.current();
    } else {
      logger.debug('Stopping audio capture (not ready)');
      stopAudioCapture();
    }
    
    return () => {
      stopAudioCapture();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isConnected, isReady, isPaused, meetingLoading, callType]);
  
  // Setup stereo audio capture: Channel 0 (left) = Microphone, Channel 1 (right) = System Audio
  // This allows Deepgram to process each channel separately and identify speakers correctly
  const setupStereoAudioCapture = useCallback((micStream: MediaStream, systemStream: MediaStream) => {
    if (!audioContextRef.current) {
      return;
    }
    const audioContext = audioContextRef.current;

    // Disconnect existing sources and processor
    if (micSourceRef.current) {
      micSourceRef.current.disconnect();
    }
    if (systemSourceRef.current) {
      systemSourceRef.current.disconnect();
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
    }
    if (trackProcessorRef.current) {
      trackProcessorRef.current.cancel().catch(() => {});
      trackProcessorRef.current = null;
    }

    // Create sources from both streams
    micSourceRef.current = audioContext.createMediaStreamSource(micStream);
    systemSourceRef.current = audioContext.createMediaStreamSource(systemStream);

    // Create a merger node to combine both sources into a stereo stream
    // Channel 0 (left) = Microphone, Channel 1 (right) = System Audio
    const merger = audioContext.createChannelMerger(2);
    micSourceRef.current.connect(merger, 0, 0); // Connect mic to channel 0 (left)
    systemSourceRef.current.connect(merger, 0, 1); // Connect system audio to channel 1 (right)

    // Create script processor for STEREO (2 channels)
    const sourceSampleRate = audioContext.sampleRate;
    const targetSampleRate = 16000;
    const needsResampling = sourceSampleRate !== targetSampleRate;
    const resampleRatio = sourceSampleRate / targetSampleRate;

    const processor = audioContext.createScriptProcessor(4096, 2, 2); // 2 input channels, 2 output channels
    processorRef.current = processor;

    processor.onaudioprocess = (event) => {
      if (isPausedRef.current || !isConnectedRef.current) {
        return;
      }

      // Get audio data from both channels
      let micData = event.inputBuffer.getChannelData(0); // Microphone (left channel)
      let systemData = event.inputBuffer.getChannelData(1); // System audio (right channel)

      // Resample both channels to 16kHz if needed
      if (needsResampling) {
        const targetLength = Math.round(micData.length / resampleRatio);
        const resampledMic = new Float32Array(targetLength);
        const resampledSystem = new Float32Array(targetLength);

        for (let i = 0; i < targetLength; i++) {
          const srcIndex = i * resampleRatio;
          const srcIndexFloor = Math.floor(srcIndex);
          const srcIndexCeil = Math.min(srcIndexFloor + 1, micData.length - 1);
          const fraction = srcIndex - srcIndexFloor;
          resampledMic[i] = micData[srcIndexFloor] * (1 - fraction) + micData[srcIndexCeil] * fraction;
          resampledSystem[i] = systemData[srcIndexFloor] * (1 - fraction) + systemData[srcIndexCeil] * fraction;
        }
        micData = resampledMic;
        systemData = resampledSystem;
      }

      // Convert to Int16 PCM and interleave as stereo (L, R, L, R, ...)
      // Each sample is 2 bytes (16-bit), so stereo is 4 bytes per sample pair
      const int16Array = new Int16Array(micData.length * 2); // 2 channels
      for (let i = 0; i < micData.length; i++) {
        // Left channel (microphone) - even indices
        const micSample = Math.max(-1, Math.min(1, micData[i]));
        int16Array[i * 2] = micSample < 0 ? micSample * 0x8000 : micSample * 0x7FFF;
        
        // Right channel (system audio) - odd indices
        const systemSample = Math.max(-1, Math.min(1, systemData[i]));
        int16Array[i * 2 + 1] = systemSample < 0 ? systemSample * 0x8000 : systemSample * 0x7FFF;
      }

      const audioBytes = new Uint8Array(int16Array.buffer);
      sendAudio(audioBytes);
    };

    // Connect merger to processor, then processor to destination
    merger.connect(processor);
    processor.connect(audioContext.destination);

    logger.info('Stereo audio capture setup: Channel 0 (left) = Microphone, Channel 1 (right) = System Audio');
  }, [sendAudio]);

  const startAudioCapture = useCallback(async () => {
    try {
      setMicError(null);
      setSystemAudioError(null);
      
      logger.info('Starting audio capture, callType:', callType);
      
      // Request microphone access
      const micStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      
      mediaStreamRef.current = micStream;
      
      // Request system audio capture based on call type
      // Google Meeting and Phone Call require system audio to capture other participants
      // In Person meetings only need microphone (no system audio needed)
      let systemStream: MediaStream | null = null;
      
      // If callType is undefined, we should still try to capture system audio as a safety measure
      // This handles cases where meetings were created before call_type was added
      const needsSystemAudio = callType === 'google_meeting' || callType === 'phone_call' || callType === undefined;
      
      logger.debug('needsSystemAudio:', needsSystemAudio, 'callType:', callType);
      
      if (needsSystemAudio) {
        // If callType is undefined, show a warning but still try to capture system audio
        if (callType === undefined) {
          logger.warn('callType is undefined - attempting system audio capture anyway');
          setSystemAudioError('Call type not specified. Attempting to capture system audio. Please allow screen sharing if prompted.');
        }
        try {
          if (isSystemAudioSupported()) {
            logger.info('Requesting system audio capture for', callType);
            systemStream = await startSystemAudioCapture();
            if (systemStream) {
              systemAudioStreamRef.current = systemStream;
              
              // Listen for when user stops sharing
              systemStream.getAudioTracks().forEach(track => {
                track.onended = () => {
                  logger.info('System audio capture ended by user');
                  systemAudioStreamRef.current = null;
                  // Restart audio capture without system audio
                  if (mediaStreamRef.current && isConnected && isReady) {
                    stopAudioCapture();
                    startAudioCapture();
                  }
                };
              });
              // Clear any previous errors if system audio capture succeeded
              setSystemAudioError(null);
            }
          } else {
            // Browser doesn't support system audio capture
            logger.warn('System audio capture not supported in this browser');
            setSystemAudioError('System audio capture not supported in this browser. Please use a browser that supports screen audio sharing (Chrome, Edge).');
          }
        } catch (err) {
          // Handle different error types gracefully
          const error = err instanceof Error ? err : new Error(String(err));
          const errorName = error.name || '';
          const errorMessage = error.message || '';
          
          // Don't show error for user denial (user clicked cancel)
          if (errorName === 'NotAllowedError' || errorMessage.includes('permission') || errorMessage.includes('denied')) {
            logger.info('User denied system audio capture');
            setSystemAudioError('System audio capture was denied. Please allow screen audio sharing to capture other participants.');
          } else {
            // Show error for other failures
            logger.warn('System audio capture failed:', err);
            setSystemAudioError(`System audio unavailable: ${errorMessage}`);
          }
          // Continue with microphone only
        }
      } else {
        // In person meeting - no system audio needed
        logger.info('In person meeting - using microphone only');
      }
      
      // If we have both streams, setup stereo capture (separate channels)
      if (systemStream && micStream) {
        // Create AudioContext for stereo capture
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
          sampleRate: 16000,
        });
        audioContextRef.current = audioContext;
        // Setup stereo capture: Channel 0 = Microphone, Channel 1 = System Audio
        setupStereoAudioCapture(micStream, systemStream);
        return; // Don't continue with normal single-stream capture
      }
      
      // Otherwise, continue with microphone only
      const stream = micStream;
      
      // Try to use MediaStreamTrackProcessor (modern API) if available
      // This avoids the ScriptProcessorNode deprecation warning
      if ('MediaStreamTrackProcessor' in window && stream.getAudioTracks().length > 0) {
        try {
          const track = stream.getAudioTracks()[0];
          const processor = new (window as any).MediaStreamTrackProcessor({ track });
          const reader = processor.readable.getReader();
          trackProcessorRef.current = reader;
          
          // Create AudioContext for format conversion
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
            sampleRate: 16000,
          });
          audioContextRef.current = audioContext;
          
          const processAudioData = async () => {
            try {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                if (isPausedRef.current || !isConnectedRef.current) {
                  value.close();
                  continue;
                }
                
                // Copy AudioData to AudioBuffer for processing
                const numberOfChannels = value.numberOfChannels;
                const numberOfFrames = value.numberOfFrames;
                const sourceSampleRate = value.sampleRate;
                
                // Create AudioBuffer and copy data
                const sourceBuffer = audioContext.createBuffer(
                  numberOfChannels,
                  numberOfFrames,
                  sourceSampleRate
                );
                
                // Copy channel data
                for (let channel = 0; channel < numberOfChannels; channel++) {
                  const channelData = sourceBuffer.getChannelData(channel);
                  value.copyTo(channelData, { planeIndex: channel });
                }
                
                // Resample to 16kHz if needed (Deepgram requires 16kHz)
                let targetBuffer = sourceBuffer;
                if (sourceSampleRate !== 16000) {
                  const targetSampleRate = 16000;
                  const ratio = sourceSampleRate / targetSampleRate;
                  const targetLength = Math.round(numberOfFrames / ratio);
                  
                  targetBuffer = audioContext.createBuffer(1, targetLength, targetSampleRate);
                  const sourceData = sourceBuffer.getChannelData(0); // Use first channel
                  const targetData = targetBuffer.getChannelData(0);
                  
                  // Simple linear interpolation resampling
                  for (let i = 0; i < targetLength; i++) {
                    const srcIndex = i * ratio;
                    const srcIndexFloor = Math.floor(srcIndex);
                    const srcIndexCeil = Math.min(srcIndexFloor + 1, numberOfFrames - 1);
                    const fraction = srcIndex - srcIndexFloor;
                    targetData[i] = sourceData[srcIndexFloor] * (1 - fraction) + sourceData[srcIndexCeil] * fraction;
                  }
                  
                  if (Math.random() < 0.01) { // Log occasionally to avoid spam
                    logger.debug(`Resampled audio: ${sourceSampleRate}Hz -> ${targetSampleRate}Hz (${numberOfFrames} -> ${targetLength} samples)`);
                  }
                }
                
                // Use first channel (mono) - already mono if we resampled
                const channelData = targetBuffer.getChannelData(0);
                
                // Calculate audio level for debugging (RMS)
                let sumSquares = 0;
                for (let i = 0; i < channelData.length; i++) {
                  sumSquares += channelData[i] * channelData[i];
                }
                const rms = Math.sqrt(sumSquares / channelData.length);
                const db = 20 * Math.log10(rms + 1e-10); // Add small epsilon to avoid log(0)
                
                // Log audio level occasionally (every 50 chunks = ~12.8 seconds at 16kHz)
                if (Math.random() < 0.02) { // 2% chance = roughly every 50 chunks
                  logger.debug(`Audio level: RMS=${rms.toFixed(4)}, dB=${db.toFixed(2)}`);
                }
                
                // Convert Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
                // Use little-endian byte order (standard for PCM)
                const int16Array = new Int16Array(channelData.length);
                for (let i = 0; i < channelData.length; i++) {
                  // Clamp to [-1, 1] and convert to 16-bit integer
                  const s = Math.max(-1, Math.min(1, channelData[i]));
                  int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                
                // Convert to bytes (little-endian, which is default for TypedArray)
                const audioBytes = new Uint8Array(int16Array.buffer);
                sendAudio(audioBytes);
                
                value.close();
              }
            } catch (err) {
              if (err instanceof Error && err.name !== 'AbortError') {
                logger.error('Error processing audio data:', err);
              }
            }
          };
          
          // Start processing in background
          processAudioData().catch(err => logger.error('Audio processing error:', err));
          
          logger.info('Audio capture started (MediaStreamTrackProcessor - modern API)');
          return;
        } catch (err) {
          logger.warn('MediaStreamTrackProcessor not available, falling back to ScriptProcessorNode:', err);
          // Continue to fallback below
        }
      }
      
      // Fallback to ScriptProcessorNode (deprecated but widely supported)
      // Note: This will show a deprecation warning, but it's the most compatible fallback
      // TODO: Migrate to AudioWorkletNode when browser support is better
      if (!audioContextRef.current) {
        // Try to create with 16kHz, but browser may use default (usually 48kHz)
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
          sampleRate: 16000,
        });
        audioContextRef.current = audioContext;
        logger.debug(`AudioContext created with sample rate: ${audioContext.sampleRate}Hz`);
      }
      const audioContext = audioContextRef.current;
      
      // Create source from microphone
      const source = audioContext.createMediaStreamSource(stream);
      
      // Create script processor to capture audio chunks
      // Buffer size: 4096 samples = ~256ms at 16kHz
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      
      // Resampling state for ScriptProcessorNode path
      const targetSampleRate = 16000;
      const sourceSampleRate = audioContext.sampleRate;
      const needsResampling = sourceSampleRate !== targetSampleRate;
      const resampleRatio = sourceSampleRate / targetSampleRate;
      
      if (needsResampling) {
        logger.debug(`Audio resampling: ${sourceSampleRate}Hz -> ${targetSampleRate}Hz`);
      }
      
      processor.onaudioprocess = (event) => {
        // Use refs to check current state (not closure values)
        if (isPausedRef.current || !isConnectedRef.current) {
          return;
        }
        
        // Get audio data (Float32Array)
        let inputData = event.inputBuffer.getChannelData(0);
        
        // Resample to 16kHz if needed
        if (needsResampling) {
          const targetLength = Math.round(inputData.length / resampleRatio);
          const resampled = new Float32Array(targetLength);
          
          // Simple linear interpolation resampling
          for (let i = 0; i < targetLength; i++) {
            const srcIndex = i * resampleRatio;
            const srcIndexFloor = Math.floor(srcIndex);
            const srcIndexCeil = Math.min(srcIndexFloor + 1, inputData.length - 1);
            const fraction = srcIndex - srcIndexFloor;
            resampled[i] = inputData[srcIndexFloor] * (1 - fraction) + inputData[srcIndexCeil] * fraction;
          }
          
          inputData = resampled;
        }
        
        // Calculate audio level for debugging (RMS)
        let sumSquares = 0;
        for (let i = 0; i < inputData.length; i++) {
          sumSquares += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sumSquares / inputData.length);
        const db = 20 * Math.log10(rms + 1e-10); // Add small epsilon to avoid log(0)
        
        // Log audio level occasionally (every 50 chunks = ~12.8 seconds at 16kHz)
        if (Math.random() < 0.02) { // 2% chance = roughly every 50 chunks
          logger.debug(`Audio level: RMS=${rms.toFixed(4)}, dB=${db.toFixed(2)}`);
        }
        
        // Convert Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
        // Use little-endian byte order (standard for PCM)
        const int16Array = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          // Clamp to [-1, 1] and convert to 16-bit integer
          const s = Math.max(-1, Math.min(1, inputData[i]));
          int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Convert to bytes (little-endian, which is default for TypedArray)
        const audioBytes = new Uint8Array(int16Array.buffer);
        sendAudio(audioBytes);
      };
      
      // Connect processor
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      logger.info('Audio capture started (ScriptProcessorNode fallback)');
    } catch (err) {
      logger.error('Error accessing microphone:', err);
      setMicError(err instanceof Error ? err.message : 'Failed to access microphone');
    }
  }, [sendAudio, setupStereoAudioCapture, callType, isConnected, isReady]);
  
  // Update ref when startAudioCapture changes
  useEffect(() => {
    startAudioCaptureRef.current = startAudioCapture;
  }, [startAudioCapture]);
  
  const stopAudioCapture = useCallback(async () => {
    // Stop system audio
    if (systemAudioStreamRef.current) {
      stopSystemAudioCapture(systemAudioStreamRef.current);
      systemAudioStreamRef.current = null;
    }
    
    // Disconnect audio sources
    if (micSourceRef.current) {
      micSourceRef.current.disconnect();
      micSourceRef.current = null;
    }
    if (systemSourceRef.current) {
      systemSourceRef.current.disconnect();
      systemSourceRef.current = null;
    }
    if (mixerNodeRef.current) {
      mixerNodeRef.current.disconnect();
      mixerNodeRef.current = null;
    }
    
    // Stop track processor reader
    if (trackProcessorRef.current) {
      try {
        await trackProcessorRef.current.cancel();
      } catch (err) {
        // Ignore errors when canceling
      }
      trackProcessorRef.current = null;
    }
    
    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    // Clear processor
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
  }, []);
  
  // Update elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isPaused) {
        setElapsed(Date.now() - startTime);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [startTime, isPaused]);
  
  // Format time as HH:MM:SS
  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };
  
  const handlePauseResume = useCallback(() => {
    if (isPaused) {
      resumeTranscription();
      setIsPaused(false);
    } else {
      pauseTranscription();
      setIsPaused(true);
    }
  }, [isPaused, pauseTranscription, resumeTranscription]);
  
  const handleEndMeeting = useCallback(async () => {
    if (window.confirm('Are you sure you want to end this meeting?')) {
      disconnect();
      navigate(`/client-calls/summary/${meetingId}`);
    }
  }, [disconnect, navigate, meetingId]);
  
  const handlePinInsight = useCallback((insightId: string) => {
    setPinnedInsights(prev => {
      const next = new Set(prev);
      if (next.has(insightId)) {
        next.delete(insightId);
      } else {
        next.add(insightId);
      }
      return next;
    });
  }, []);
  
  const handleAddActionItem = useCallback((item: string) => {
    setActionItems(prev => [...prev, item]);
  }, []);
  
  if (meetingLoading || isConnecting) {
    return (
      <div className="live-meeting-container">
        <Loader text={meetingLoading ? "Loading meeting..." : "Connecting to meeting..."} />
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="live-meeting-container">
        <div className="form-error" style={{ margin: '2rem' }}>
          <strong>Connection Error:</strong> {error}
          <button className="btn-primary" onClick={() => connect(meetingId!)} style={{ marginTop: '1rem' }}>
            Retry Connection
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="live-meeting-container">
      {/* Header */}
      <header className="live-meeting-header">
        <div>
          <h1>{MOCK_CONTEXT.company.name} - Live Meeting</h1>
        </div>
        
        <div className={`meeting-timer ${isPaused ? 'paused' : 'recording'}`}>
          <span className={`recording-dot ${isPaused ? 'paused' : 'active'}`} />
          <span>{formatTime(elapsed)}</span>
          <span>{isPaused ? 'Paused' : 'Recording'}</span>
        </div>
        
        {/* Info message for call types requiring system audio */}
        {(callType === 'google_meeting' || callType === 'phone_call') && (
          <div className="call-type-info" style={{ 
            margin: '0.5rem 0', 
            padding: '0.75rem', 
            backgroundColor: 'var(--color-info-light)', 
            borderRadius: 'var(--border-radius-md)',
            fontSize: '0.875rem',
            color: 'var(--color-info)'
          }}>
            <strong>📢 System Audio Required:</strong> When prompted, please select "Share system audio" or "Share tab audio" 
            so Nebula can listen to {callType === 'google_meeting' ? 'the meeting' : 'the call'}.
          </div>
        )}
        
        {callType === 'in_person' && (
          <div className="call-type-info" style={{ 
            margin: '0.5rem 0', 
            padding: '0.75rem', 
            backgroundColor: 'var(--color-success-light)', 
            borderRadius: 'var(--border-radius-md)',
            fontSize: '0.875rem',
            color: 'var(--color-success)'
          }}>
            <strong>✅ In Person Meeting:</strong> No screen audio sharing required. Just ensure Nebula is listening while you speak.
          </div>
        )}
        
        {/* System Audio Status/Error with Retry */}
        {systemAudioError && (callType === 'google_meeting' || callType === 'phone_call') && (
          <div className="system-audio-status" style={{ 
            margin: '0.5rem 0', 
            padding: '0.75rem',
            backgroundColor: 'var(--color-warning-light)',
            borderRadius: 'var(--border-radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
          }}>
            <div style={{ fontSize: '0.875rem', color: 'var(--color-warning-dark)' }}>
              ⚠️ {systemAudioError} (continuing with microphone only)
            </div>
            <button
              className="btn-secondary"
              onClick={async () => {
                setSystemAudioError(null);
                // Retry system audio capture
                try {
                  if (isSystemAudioSupported()) {
                    const systemStream = await startSystemAudioCapture();
                    if (systemStream && mediaStreamRef.current) {
                      systemAudioStreamRef.current = systemStream;
                      // Setup stereo capture with existing mic stream
                      if (!audioContextRef.current) {
                        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
                          sampleRate: 16000,
                        });
                      }
                      setupStereoAudioCapture(mediaStreamRef.current, systemStream);
                      setSystemAudioError(null);
                    }
                  }
                } catch (err) {
                  const error = err instanceof Error ? err : new Error(String(err));
                  setSystemAudioError(`Retry failed: ${error.message}`);
                }
              }}
              style={{ 
                padding: '0.375rem 0.75rem', 
                fontSize: '0.75rem',
                whiteSpace: 'nowrap',
              }}
            >
              🔄 Retry System Audio
            </button>
          </div>
        )}
        
        <div className="meeting-controls">
          <button
            className="meeting-control-btn secondary"
            onClick={handlePauseResume}
          >
            {isPaused ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                Resume
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16"/>
                  <rect x="14" y="4" width="4" height="16"/>
                </svg>
                Pause
              </>
            )}
          </button>
          <button
            className="meeting-control-btn danger"
            onClick={handleEndMeeting}
          >
            End Meeting
          </button>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="live-meeting-main">
        {/* Transcript Panel */}
        <div className="live-meeting-panel">
          <div className="panel-header">
            Live Transcript
            {!isConnected && <span style={{ color: 'var(--color-warning)', marginLeft: '8px' }}>(Disconnected)</span>}
            {micError && <span style={{ color: 'var(--color-error)', marginLeft: '8px' }}>(Mic Error)</span>}
          </div>
          {micError && (
            <div className="form-error" style={{ margin: '1rem', padding: '0.75rem' }}>
              <strong>Microphone Error:</strong> {micError}
              <button 
                className="btn-primary" 
                onClick={startAudioCapture} 
                style={{ marginTop: '0.5rem', display: 'block' }}
              >
                Retry Microphone Access
              </button>
            </div>
          )}
          <div className="panel-content">
            <LiveTranscript entries={transcript} />
          </div>
        </div>
        
        {/* Insights Panel */}
        <div className="live-meeting-panel">
          <div className="panel-header">AI Insights</div>
          <div className="panel-content">
            <LiveInsights
              insights={insights}
              pinnedIds={pinnedInsights}
              onPin={handlePinInsight}
              onAddActionItem={handleAddActionItem}
            />
          </div>
        </div>
        
        {/* Context Panel */}
        <div className="live-meeting-panel">
          <div className="panel-header">Meeting Context</div>
          <div className="panel-content">
            <MeetingContext context={MOCK_CONTEXT} actionItems={actionItems} />
          </div>
        </div>
      </main>
    </div>
  );
};
