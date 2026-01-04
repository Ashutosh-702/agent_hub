import { useRef, useEffect, useState } from 'react';
import type { TranscriptEntry } from './useMeetingWebSocket';

interface LiveTranscriptProps {
  entries: TranscriptEntry[];
}

// Format timestamp in MM:SS
const formatTimestamp = (timestamp: number) => {
  const minutes = Math.floor(timestamp / 60);
  const seconds = Math.floor(timestamp % 60);
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

export const LiveTranscript = ({ entries }: LiveTranscriptProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  
  // Process entries to handle interim/final updates while preserving full history
  // Only merge interim transcripts that are from the same speaker and consecutive
  const processedEntries = entries.reduce((acc, entry) => {
    const prevEntry = acc[acc.length - 1];
    
    // Skip empty transcripts
    if (!entry.text || !entry.text.trim()) {
      return acc;
    }
    
    // If this is an interim transcript, check if we should update the last entry
    if (!entry.isFinal && prevEntry && !prevEntry.isFinal && prevEntry.speaker === entry.speaker) {
      // Check if this is a continuation/update of the previous interim (same timestamp window)
      const timeDiff = Math.abs(entry.timestamp - prevEntry.timestamp);
      if (timeDiff < 2.0) { // Within 2 seconds, likely an update
        // Update the last interim entry instead of adding a new one
        acc[acc.length - 1] = {
          ...prevEntry,
          text: entry.text, // Update with latest interim text
          timestamp: entry.timestamp, // Update timestamp
        };
        return acc;
      }
    }
    
    // If this is a final transcript and previous was interim from same speaker, replace it
    if (entry.isFinal && prevEntry && !prevEntry.isFinal && prevEntry.speaker === entry.speaker) {
      const timeDiff = Math.abs(entry.timestamp - prevEntry.timestamp);
      if (timeDiff < 3.0) { // Within 3 seconds, likely the finalization
        // Replace interim with final
        acc[acc.length - 1] = {
          ...entry,
          id: prevEntry.id, // Keep the same ID
        };
        return acc;
      }
    }
    
    // Add as new entry (preserve all final transcripts and distinct interim ones)
    acc.push(entry);
    return acc;
  }, [] as typeof entries);
  
  // Auto-scroll to bottom when new entries arrive (only if user hasn't scrolled up)
  useEffect(() => {
    if (containerRef.current && shouldAutoScroll) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [processedEntries, shouldAutoScroll]);
  
  // Check if user has scrolled up
  const handleScroll = () => {
    if (!containerRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50; // 50px threshold
    
    setShouldAutoScroll(isAtBottom);
    setShowScrollButton(!isAtBottom);
  };
  
  // Scroll to bottom button handler
  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: 'smooth',
      });
      setShouldAutoScroll(true);
      setShowScrollButton(false);
    }
  };
  
  if (processedEntries.length === 0) {
    return (
      <div className="insights-empty">
        <div className="insights-empty-icon">🎤</div>
        <p>Waiting for speech...</p>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-gray-400)', marginTop: '0.5rem' }}>
          The transcript will appear here as you speak
        </p>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div 
        ref={containerRef} 
        className="transcript-container"
        onScroll={handleScroll}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        {processedEntries.map((entry) => {
          const isUser = entry.speaker === 'user';
          const sourceLabel = entry.source === 'mic' ? 'Mic' : 'System Audio';
          
          return (
            <div 
              key={entry.id || `entry-${entry.timestamp}-${entry.text.slice(0, 10)}`}
              style={{
                display: 'flex',
                justifyContent: isUser ? 'flex-end' : 'flex-start',
                marginBottom: '0.5rem',
              }}
            >
              <div
                style={{
                  maxWidth: '75%',
                  padding: '0.75rem 1rem',
                  borderRadius: '12px',
                  backgroundColor: isUser 
                    ? 'var(--color-primary)' 
                    : 'var(--color-gray-100)',
                  color: isUser 
                    ? 'white' 
                    : 'var(--color-gray-900)',
                  boxShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
                  opacity: entry.isFinal ? 1 : 0.7,
                }}
              >
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem',
                  marginBottom: '0.25rem',
                  fontSize: '0.75rem',
                  opacity: 0.8,
                }}>
                  <span style={{ fontWeight: 600 }}>
                    {isUser ? 'You' : 'Client'}
                  </span>
                  <span style={{ fontSize: '0.7rem' }}>
                    ({sourceLabel})
                  </span>
                  <span style={{ marginLeft: 'auto', fontSize: '0.7rem' }}>
                    {formatTimestamp(entry.timestamp)}
                  </span>
                  {!entry.isFinal && (
                    <span style={{ fontSize: '0.7rem' }}>...</span>
                  )}
                </div>
                <div style={{ 
                  fontSize: '0.9rem',
                  lineHeight: '1.5',
                  wordBreak: 'break-word',
                }}>
                  {entry.text}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          style={{
            position: 'absolute',
            bottom: '1rem',
            right: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: 'var(--color-primary)',
            color: 'white',
            border: 'none',
            borderRadius: '20px',
            cursor: 'pointer',
            fontSize: '0.875rem',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
            zIndex: 10,
          }}
        >
          ↓ Scroll to bottom
        </button>
      )}
    </div>
  );
};

