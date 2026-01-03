import { useRef, useEffect } from 'react';
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
  
  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [entries]);
  
  if (entries.length === 0) {
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

  return (
    <div ref={containerRef} className="transcript-container">
      {processedEntries.length === 0 ? (
        <div className="insights-empty">
          <div className="insights-empty-icon">🎤</div>
          <p>Waiting for speech...</p>
          <p style={{ fontSize: '0.75rem', color: 'var(--color-gray-400)', marginTop: '0.5rem' }}>
            The transcript will appear here as you speak
          </p>
        </div>
      ) : (
        processedEntries.map((entry) => (
          <div 
            key={entry.id || `entry-${entry.timestamp}-${entry.text.slice(0, 10)}`} 
            className={`transcript-message ${entry.speaker === 'user' ? 'transcript-message-user' : 'transcript-message-client'}`}
          >
            <div className="transcript-message-header">
              <span className={`transcript-speaker ${entry.speaker === 'user' ? 'user' : 'client'}`}>
                {entry.speaker === 'user' ? 'You' : 'Client'}
              </span>
              <span className="transcript-timestamp">{formatTimestamp(entry.timestamp)}</span>
              {!entry.isFinal && <span className="transcript-interim-badge">...</span>}
            </div>
            <div className={`transcript-message-content ${entry.isFinal === false ? 'transcript-interim' : ''}`}>
              {entry.text}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

