import { useState, useCallback, useRef, useEffect } from 'react';
import { wsLogger as logger } from '../../utils/logger';

export interface TranscriptEntry {
  id: string;
  speaker: 'user' | 'client';
  text: string;
  timestamp: number;
  isFinal: boolean;
}

export interface Insight {
  id: string;
  type: 'objection_detected' | 'buying_signal' | 'competitor_mention' | 'pricing_question' |
        'timeline_question' | 'product_opportunity' | 'next_step_suggestion' | 'risk_flag' |
        'discovery_opportunity' | 'feature_interest';
  message: string;
  suggestedResponse?: string;
  timestamp: number;
  confidence: number;
}

interface WebSocketMessage {
  type: 'transcript' | 'transcript_final' | 'transcript_interim' | 'insight' | 'error' | 'status';
  data?: any;
  text?: string;
  transcript?: string;
  speaker?: string;
  timestamp?: number;
  insight?: any;
  message?: string;
}

export const useMeetingWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isReady, setIsReady] = useState(false); // Track when Deepgram is ready
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const meetingIdRef = useRef<string | null>(null);
  const connectingRef = useRef(false);
  const connectedRef = useRef(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Connect to WebSocket
  const connect = useCallback(async (meetingId: string) => {
    // Prevent multiple connection attempts
    if (connectingRef.current || connectedRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    connectingRef.current = true;
    setIsConnecting(true);
    setError(null);
    meetingIdRef.current = meetingId;
    
    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    try {
      // WebSocket URL - matches backend route at /ws/meetings/{meeting_id}
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/meetings/${meetingId}`;
      logger.info(`Connecting to WebSocket: ${wsUrl}`);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        logger.info('WebSocket connected successfully');
        connectedRef.current = true;
        connectingRef.current = false;
        setIsConnected(true);
        setIsConnecting(false);
        wsRef.current = ws;
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          if (message.type === 'transcript' || message.type === 'transcript_final' || message.type === 'transcript_interim') {
            const transcriptText = message.text || message.transcript || '';
            const timestamp = message.timestamp || Date.now() / 1000;
            const speaker = (message.speaker === 'client' ? 'client' : 'user') as 'user' | 'client';
            const isFinal = message.type === 'transcript_final';
            
            // Skip empty transcripts
            if (!transcriptText.trim()) {
              return;
            }
            
            if (message.data) {
              // If data is provided, use it directly
              setTranscript(prev => {
                // For interim transcripts, replace the last interim entry if it exists
                if (!isFinal) {
                  const lastEntry = prev[prev.length - 1];
                  if (lastEntry && !lastEntry.isFinal && lastEntry.speaker === speaker) {
                    // Update the last interim entry
                    return [...prev.slice(0, -1), { ...lastEntry, text: transcriptText, timestamp }];
                  }
                }
                // For final transcripts or if no interim entry exists, add new entry
                return [...prev, { ...message.data, isFinal }];
              });
            } else {
              // Handle direct transcript data
              setTranscript(prev => {
                // For interim transcripts, replace the last interim entry if it exists
                if (!isFinal) {
                  const lastEntry = prev[prev.length - 1];
                  if (lastEntry && !lastEntry.isFinal && lastEntry.speaker === speaker) {
                    // Update the last interim entry instead of adding a new one
                    return [...prev.slice(0, -1), {
                      ...lastEntry,
                      text: transcriptText,
                      timestamp,
                    }];
                  }
                }
                
                // For final transcripts, check if we should replace the last interim entry
                if (isFinal) {
                  const lastEntry = prev[prev.length - 1];
                  if (lastEntry && !lastEntry.isFinal && lastEntry.speaker === speaker) {
                    // Replace interim with final
                    return [...prev.slice(0, -1), {
                      id: lastEntry.id || `transcript-${Date.now()}`,
                      speaker,
                      text: transcriptText,
                      timestamp,
                      isFinal: true,
                    }];
                  }
                }
                
                // Add new entry
                return [...prev, {
                  id: `transcript-${Date.now()}-${Math.random()}`,
                  speaker,
                  text: transcriptText,
                  timestamp,
                  isFinal,
                }];
              });
            }
          } else if (message.type === 'insight') {
            if (message.data) {
              setInsights(prev => [...prev, message.data]);
            } else if (message.insight) {
              setInsights(prev => [...prev, message.insight]);
            }
          } else if (message.type === 'error') {
            const errorMsg = message.data?.message || message.message || 'Unknown error';
            setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
          } else if (message.type === 'status') {
            // Status messages - check if Deepgram is ready
            const statusData = message.data || message;
            const statusMessage = typeof statusData === 'string' ? statusData : statusData.message || '';
            if (statusMessage.includes('initialized') || statusMessage.includes('connected')) {
              setIsReady(true);
              logger.info('Deepgram ready, audio capture can start');
            }
            logger.debug('WebSocket status:', statusData);
          }
        } catch (err) {
          logger.error('Failed to parse WebSocket message:', err);
        }
      };
      
      ws.onerror = (error) => {
        logger.error('WebSocket connection error:', error);
        logger.debug('WebSocket readyState:', ws.readyState);
        connectingRef.current = false;
        setIsConnecting(false);
        setError('Failed to connect to meeting. Please check your connection and try again.');
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
        ws.close();
      };
      
      ws.onclose = (event) => {
        logger.info('WebSocket closed:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          wasConnected: connectedRef.current,
        });
        
        if (!connectedRef.current) {
          // Connection never opened - show error
          connectingRef.current = false;
          setIsConnecting(false);
          if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
          }
          if (event.code !== 1000) { // 1000 is normal closure
            const errorMsg = event.reason || `Connection failed (code: ${event.code}). Please check if the meeting exists and the server is running.`;
            setError(errorMsg);
          }
        } else {
          // Connection was open but closed
          setIsConnected(false);
          if (event.code !== 1000) {
            setError('Connection lost. Please refresh the page to reconnect.');
          }
        }
        wsRef.current = null;
      };
      
      // Set timeout for connection (use refs to check current state)
      timeoutRef.current = setTimeout(() => {
        if (connectingRef.current && !connectedRef.current) {
          // Connection timed out
          logger.error('WebSocket connection timed out');
          logger.debug('WebSocket readyState:', ws.readyState);
          logger.debug('WebSocket URL:', wsUrl);
          connectingRef.current = false;
          setIsConnecting(false);
          
          // Provide more specific error message based on readyState
          let errorMsg = 'Connection timeout. ';
          if (ws.readyState === WebSocket.CONNECTING) {
            errorMsg += 'The server is not responding. Please check if the backend server is running and the meeting ID is valid.';
          } else if (ws.readyState === WebSocket.CLOSED) {
            errorMsg += 'Connection was closed. Please check server logs for details.';
          } else {
            errorMsg += 'Please check your network connection and try again.';
          }
          setError(errorMsg);
          
          if (ws.readyState !== WebSocket.OPEN) {
            ws.close();
          }
        }
      }, 10000); // Increased timeout to 10 seconds for production
      
    } catch (err) {
      // WebSocket creation failed
      connectingRef.current = false;
      setIsConnecting(false);
      setError(`Failed to establish connection: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, []);
  
  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    
    // Reset refs
    connectingRef.current = false;
    connectedRef.current = false;
    setIsConnected(false);
    setIsConnecting(false);
  }, []);
  
  // Send audio data (accepts Blob or Uint8Array)
  const sendAudio = useCallback((audioData: Blob | Uint8Array) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioData);
    }
  }, []);
  
  // Pause transcription
  const pauseTranscription = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'pause' }));
    } else {
      setError('Cannot pause: not connected to meeting');
    }
  }, []);
  
  // Resume transcription
  const resumeTranscription = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'resume' }));
    } else {
      setError('Cannot resume: not connected to meeting');
    }
  }, []);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);
  
  return {
    isConnected,
    isConnecting,
    isReady,
    transcript,
    insights,
    error,
    connect,
    disconnect,
    sendAudio,
    pauseTranscription,
    resumeTranscription,
  };
};
