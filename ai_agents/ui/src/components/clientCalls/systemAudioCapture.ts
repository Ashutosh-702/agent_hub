/**
 * System Audio Capture Helper
 * 
 * Captures system audio (speakers/other participants) using getDisplayMedia
 * and mixes it with microphone input for complete conversation transcription.
 */

import { audioLogger as logger } from '../../utils/logger';

export interface SystemAudioCapture {
  start: () => Promise<MediaStream | null>;
  stop: () => void;
  isSupported: () => boolean;
}

/**
 * Check if system audio capture is supported
 */
export const isSystemAudioSupported = (): boolean => {
  return 'getDisplayMedia' in navigator.mediaDevices;
};

/**
 * Start capturing system audio
 * This will prompt the user to share system audio
 */
export const startSystemAudioCapture = async (): Promise<MediaStream | null> => {
  if (!isSystemAudioSupported()) {
    throw new Error('System audio capture is not supported in this browser');
  }

  try {
    // Request system audio capture using getDisplayMedia
    // Note: Some browsers require video: true even if we only need audio
    // We'll request both and then stop the video track if we get one
    const systemStream = await navigator.mediaDevices.getDisplayMedia({
      video: true, // Some browsers require this even for audio-only
      audio: {
        echoCancellation: false,
        noiseSuppression: false,
        autoGainControl: false,
        suppressLocalAudioPlayback: false, // Allow system audio to play
      } as MediaTrackConstraints,
    });

    // Stop video tracks if we got any (we only need audio)
    systemStream.getVideoTracks().forEach(track => {
      track.stop();
      systemStream.removeTrack(track);
    });

    // Check if we actually got audio tracks
    if (systemStream.getAudioTracks().length === 0) {
      throw new Error('No audio tracks available in system audio stream');
    }

    logger.info('System audio capture started');
    return systemStream;
  } catch (err) {
    logger.error('Error capturing system audio:', err);
    throw err;
  }
};

/**
 * Stop system audio capture
 */
export const stopSystemAudioCapture = (stream: MediaStream | null): void => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    logger.info('System audio capture stopped');
  }
};

/**
 * Mix microphone and system audio streams
 * Returns a MediaStream with the mixed audio
 */
export const mixAudioStreams = (
  micStream: MediaStream,
  systemStream: MediaStream,
  audioContext: AudioContext
): {
  mixedSource: MediaStreamAudioSourceNode;
  cleanup: () => void;
} => {
  // Create sources from both streams
  const micSource = audioContext.createMediaStreamSource(micStream);
  const systemSource = audioContext.createMediaStreamSource(systemStream);

  // Create a gain node to mix both sources
  const mixerNode = audioContext.createGain();
  mixerNode.gain.value = 1.0;

  // Connect both sources to the mixer
  micSource.connect(mixerNode);
  systemSource.connect(mixerNode);

  // Create a MediaStreamDestination to get the mixed audio as a stream
  const destination = audioContext.createMediaStreamDestination();
  mixerNode.connect(destination);

  const cleanup = () => {
    micSource.disconnect();
    systemSource.disconnect();
    mixerNode.disconnect();
  };

  return {
    mixedSource: destination.stream as any, // The destination stream contains mixed audio
    cleanup,
  };
};

