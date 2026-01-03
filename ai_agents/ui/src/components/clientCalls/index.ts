// Client Calls Module - Components Index

export { ClientCallsPage } from './ClientCallsPage';
export { StartMeetingForm } from './StartMeetingForm';
export { LiveMeetingScreen } from './LiveMeetingScreen';
export { LiveTranscript } from './LiveTranscript';
export { LiveInsights } from './LiveInsights';
export { MeetingContext } from './MeetingContext';
export { PostCallSummary } from './PostCallSummary';
export { PostCallReflections } from './PostCallReflections';
export { ReflectionsView } from './ReflectionsView';
export { PrepMeetingForm } from './PrepMeetingForm';
export { BattlecardView } from './BattlecardView';
export { MeetingHistory } from './MeetingHistory';
export { PhoneCallPage } from './PhoneCallPage';
export { StartPhoneCallForm } from './StartPhoneCallForm';
export { LogPhoneCallForm } from './LogPhoneCallForm';
export { useMeetingWebSocket } from './useMeetingWebSocket';
export type { TranscriptEntry, Insight } from './useMeetingWebSocket';

// Shared mock data and utilities
export { 
  PRODUCTS, 
  MOCK_COMPANIES, 
  MOCK_CONTACTS_BY_COMPANY,
  DEFAULT_MOCK_CONTACTS,
  getContactsForCompany,
  DEFAULT_MEETING_CONTEXT,
  DEFAULT_MEETING_SUMMARY,
} from './mockData';
export type { MockContact, MockCompany, MeetingContextData, MeetingSummaryData } from './mockData';

// Audio capture utilities
export { 
  isAudioWorkletSupported,
  createAudioCapture,
  connectMicrophoneStream,
  connectStereoStreams,
  pauseCapture,
  resumeCapture,
  stopCapture,
} from './audioWorklet';
export type { AudioCaptureConfig, AudioCaptureState } from './audioWorklet';
