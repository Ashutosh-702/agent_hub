/**
 * Audio Worklet Processor for real-time audio capture
 * 
 * This module provides a modern AudioWorkletNode-based audio capture
 * that replaces the deprecated ScriptProcessorNode.
 */

import { audioLogger as logger } from '../../utils/logger';

// Audio Worklet Processor code as a string (will be converted to Blob URL)
const audioProcessorCode = `
class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 4096;
    this.buffer = new Float32Array(this.bufferSize);
    this.bufferIndex = 0;
    this.isStereo = false;
    this.stereoBuffer = null;
    
    this.port.onmessage = (event) => {
      if (event.data.type === 'config') {
        this.isStereo = event.data.isStereo || false;
        if (this.isStereo) {
          this.stereoBuffer = [
            new Float32Array(this.bufferSize),
            new Float32Array(this.bufferSize)
          ];
        }
      }
    };
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || input.length === 0) {
      return true;
    }

    if (this.isStereo && input.length >= 2) {
      // Stereo processing
      const leftChannel = input[0];
      const rightChannel = input[1];
      
      for (let i = 0; i < leftChannel.length; i++) {
        if (this.bufferIndex < this.bufferSize) {
          this.stereoBuffer[0][this.bufferIndex] = leftChannel[i];
          this.stereoBuffer[1][this.bufferIndex] = rightChannel[i] || 0;
          this.bufferIndex++;
        }
        
        if (this.bufferIndex >= this.bufferSize) {
          // Send stereo buffer
          this.port.postMessage({
            type: 'audio',
            leftChannel: this.stereoBuffer[0].slice(),
            rightChannel: this.stereoBuffer[1].slice(),
            isStereo: true
          });
          this.bufferIndex = 0;
        }
      }
    } else {
      // Mono processing
      const channelData = input[0];
      
      for (let i = 0; i < channelData.length; i++) {
        this.buffer[this.bufferIndex++] = channelData[i];
        
        if (this.bufferIndex >= this.bufferSize) {
          // Send buffer to main thread
          this.port.postMessage({
            type: 'audio',
            buffer: this.buffer.slice(),
            isStereo: false
          });
          this.bufferIndex = 0;
        }
      }
    }

    return true;
  }
}

registerProcessor('audio-capture-processor', AudioCaptureProcessor);
`;

// Check if AudioWorklet is supported
export const isAudioWorkletSupported = (): boolean => {
  return 'AudioWorklet' in window && 'AudioWorkletNode' in window;
};

// Create a Blob URL for the audio worklet processor
let workletBlobUrl: string | null = null;

const getWorkletUrl = (): string => {
  if (!workletBlobUrl) {
    const blob = new Blob([audioProcessorCode], { type: 'application/javascript' });
    workletBlobUrl = URL.createObjectURL(blob);
  }
  return workletBlobUrl;
};

// Audio capture configuration
export interface AudioCaptureConfig {
  targetSampleRate: number;
  onAudioData: (audioBytes: Uint8Array) => void;
  onError?: (error: Error) => void;
  isStereo?: boolean;
}

// Audio capture state
export interface AudioCaptureState {
  audioContext: AudioContext | null;
  workletNode: AudioWorkletNode | null;
  micSource: MediaStreamAudioSourceNode | null;
  systemSource: MediaStreamAudioSourceNode | null;
  merger: ChannelMergerNode | null;
  micStream: MediaStream | null;
  systemStream: MediaStream | null;
  isPaused: boolean;
  isConnected: boolean;
}

/**
 * Convert Float32 audio to Int16 PCM bytes
 */
const convertToInt16PCM = (
  float32Data: Float32Array,
  float32Data2?: Float32Array
): Uint8Array => {
  if (float32Data2) {
    // Stereo: interleave L, R, L, R, ...
    const int16Array = new Int16Array(float32Data.length * 2);
    for (let i = 0; i < float32Data.length; i++) {
      // Left channel (microphone)
      const leftSample = Math.max(-1, Math.min(1, float32Data[i]));
      int16Array[i * 2] = leftSample < 0 ? leftSample * 0x8000 : leftSample * 0x7FFF;
      
      // Right channel (system audio)
      const rightSample = Math.max(-1, Math.min(1, float32Data2[i]));
      int16Array[i * 2 + 1] = rightSample < 0 ? rightSample * 0x8000 : rightSample * 0x7FFF;
    }
    return new Uint8Array(int16Array.buffer);
  } else {
    // Mono
    const int16Array = new Int16Array(float32Data.length);
    for (let i = 0; i < float32Data.length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Data[i]));
      int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
    }
    return new Uint8Array(int16Array.buffer);
  }
};

/**
 * Resample audio from source rate to target rate using linear interpolation
 */
const resampleAudio = (
  sourceData: Float32Array,
  sourceSampleRate: number,
  targetSampleRate: number
): Float32Array => {
  if (sourceSampleRate === targetSampleRate) {
    return sourceData;
  }
  
  const ratio = sourceSampleRate / targetSampleRate;
  const targetLength = Math.round(sourceData.length / ratio);
  const targetData = new Float32Array(targetLength);
  
  for (let i = 0; i < targetLength; i++) {
    const srcIndex = i * ratio;
    const srcIndexFloor = Math.floor(srcIndex);
    const srcIndexCeil = Math.min(srcIndexFloor + 1, sourceData.length - 1);
    const fraction = srcIndex - srcIndexFloor;
    targetData[i] = sourceData[srcIndexFloor] * (1 - fraction) + sourceData[srcIndexCeil] * fraction;
  }
  
  return targetData;
};

/**
 * Create AudioWorklet-based audio capture
 */
export const createAudioCapture = async (
  config: AudioCaptureConfig
): Promise<AudioCaptureState> => {
  const state: AudioCaptureState = {
    audioContext: null,
    workletNode: null,
    micSource: null,
    systemSource: null,
    merger: null,
    micStream: null,
    systemStream: null,
    isPaused: false,
    isConnected: false,
  };

  try {
    // Create AudioContext
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    state.audioContext = new AudioContextClass({
      sampleRate: 48000, // Browser native rate, we'll resample
    });

    if (isAudioWorkletSupported()) {
      // Load the audio worklet module
      await state.audioContext.audioWorklet.addModule(getWorkletUrl());
      logger.info('AudioWorklet module loaded successfully');

      // Create the worklet node
      state.workletNode = new AudioWorkletNode(
        state.audioContext,
        'audio-capture-processor',
        {
          numberOfInputs: 1,
          numberOfOutputs: 1,
          channelCount: config.isStereo ? 2 : 1,
          channelCountMode: 'explicit',
        }
      );

      // Configure stereo mode
      state.workletNode.port.postMessage({
        type: 'config',
        isStereo: config.isStereo || false,
      });

      // Handle audio data from worklet
      state.workletNode.port.onmessage = (event) => {
        if (event.data.type === 'audio' && state.isConnected && !state.isPaused) {
          const sourceSampleRate = state.audioContext?.sampleRate || 48000;
          
          if (event.data.isStereo) {
            // Resample both channels
            const leftResampled = resampleAudio(
              new Float32Array(event.data.leftChannel),
              sourceSampleRate,
              config.targetSampleRate
            );
            const rightResampled = resampleAudio(
              new Float32Array(event.data.rightChannel),
              sourceSampleRate,
              config.targetSampleRate
            );
            const audioBytes = convertToInt16PCM(leftResampled, rightResampled);
            config.onAudioData(audioBytes);
          } else {
            // Mono processing
            const resampled = resampleAudio(
              new Float32Array(event.data.buffer),
              sourceSampleRate,
              config.targetSampleRate
            );
            const audioBytes = convertToInt16PCM(resampled);
            config.onAudioData(audioBytes);
          }
        }
      };

      logger.info('AudioWorklet capture initialized');
    } else {
      logger.warn('AudioWorklet not supported, will use ScriptProcessorNode fallback');
    }

    state.isConnected = true;
    return state;
  } catch (error) {
    logger.error('Failed to create audio capture:', error);
    if (config.onError) {
      config.onError(error instanceof Error ? error : new Error(String(error)));
    }
    throw error;
  }
};

/**
 * Connect microphone stream to audio capture
 */
export const connectMicrophoneStream = (
  state: AudioCaptureState,
  micStream: MediaStream
): void => {
  if (!state.audioContext) {
    throw new Error('AudioContext not initialized');
  }

  state.micStream = micStream;
  state.micSource = state.audioContext.createMediaStreamSource(micStream);

  if (state.workletNode) {
    state.micSource.connect(state.workletNode);
    state.workletNode.connect(state.audioContext.destination);
    logger.info('Microphone connected via AudioWorklet');
  }
};

/**
 * Connect stereo streams (mic + system audio) to audio capture
 */
export const connectStereoStreams = (
  state: AudioCaptureState,
  micStream: MediaStream,
  systemStream: MediaStream
): void => {
  if (!state.audioContext) {
    throw new Error('AudioContext not initialized');
  }

  state.micStream = micStream;
  state.systemStream = systemStream;

  // Create sources
  state.micSource = state.audioContext.createMediaStreamSource(micStream);
  state.systemSource = state.audioContext.createMediaStreamSource(systemStream);

  // Create channel merger (2 channels)
  state.merger = state.audioContext.createChannelMerger(2);

  // Connect: mic -> channel 0 (left), system -> channel 1 (right)
  state.micSource.connect(state.merger, 0, 0);
  state.systemSource.connect(state.merger, 0, 1);

  if (state.workletNode) {
    state.merger.connect(state.workletNode);
    state.workletNode.connect(state.audioContext.destination);
    logger.info('Stereo streams connected via AudioWorklet');
  }
};

/**
 * Pause audio capture
 */
export const pauseCapture = (state: AudioCaptureState): void => {
  state.isPaused = true;
};

/**
 * Resume audio capture
 */
export const resumeCapture = (state: AudioCaptureState): void => {
  state.isPaused = false;
};

/**
 * Stop and clean up audio capture
 */
export const stopCapture = (state: AudioCaptureState): void => {
  state.isConnected = false;
  state.isPaused = true;

  // Disconnect sources
  if (state.micSource) {
    state.micSource.disconnect();
    state.micSource = null;
  }
  if (state.systemSource) {
    state.systemSource.disconnect();
    state.systemSource = null;
  }
  if (state.merger) {
    state.merger.disconnect();
    state.merger = null;
  }

  // Stop worklet
  if (state.workletNode) {
    state.workletNode.disconnect();
    state.workletNode.port.close();
    state.workletNode = null;
  }

  // Stop media streams
  if (state.micStream) {
    state.micStream.getTracks().forEach(track => track.stop());
    state.micStream = null;
  }
  if (state.systemStream) {
    state.systemStream.getTracks().forEach(track => track.stop());
    state.systemStream = null;
  }

  // Close audio context
  if (state.audioContext && state.audioContext.state !== 'closed') {
    state.audioContext.close().catch(() => {});
    state.audioContext = null;
  }

  logger.info('Audio capture stopped and cleaned up');
};

/**
 * Fallback: Create ScriptProcessorNode-based capture for older browsers
 */
export const createScriptProcessorCapture = (
  audioContext: AudioContext,
  config: AudioCaptureConfig,
  isStereo: boolean = false
): ScriptProcessorNode => {
  const bufferSize = 4096;
  const inputChannels = isStereo ? 2 : 1;
  const outputChannels = isStereo ? 2 : 1;
  
  const processor = audioContext.createScriptProcessor(bufferSize, inputChannels, outputChannels);
  
  const sourceSampleRate = audioContext.sampleRate;
  const targetSampleRate = config.targetSampleRate;

  processor.onaudioprocess = (event) => {
    if (isStereo) {
      // Stereo processing
      let leftData = event.inputBuffer.getChannelData(0);
      let rightData = event.inputBuffer.getChannelData(1);
      
      // Resample
      leftData = resampleAudio(leftData, sourceSampleRate, targetSampleRate);
      rightData = resampleAudio(rightData, sourceSampleRate, targetSampleRate);
      
      const audioBytes = convertToInt16PCM(leftData, rightData);
      config.onAudioData(audioBytes);
    } else {
      // Mono processing
      let channelData = event.inputBuffer.getChannelData(0);
      channelData = resampleAudio(channelData, sourceSampleRate, targetSampleRate);
      const audioBytes = convertToInt16PCM(channelData);
      config.onAudioData(audioBytes);
    }
  };

  return processor;
};

