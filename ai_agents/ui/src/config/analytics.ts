/**
 * Analytics and Monitoring Configuration
 * 
 * Integrates:
 * - Zipy.ai: Session recording and error monitoring
 * - Usersnap: Bug reporting and user feedback
 */

// Get keys from environment config or window.ENV_CONFIG
declare global {
  interface Window {
    ENV_CONFIG?: {
      ZIPY_PROJECT_KEY?: string;
      USERSNAP_PROJECT_KEY?: string;
      [key: string]: string | undefined;
    };
  }
}

// Default project keys (can be overridden via env variables)
const DEFAULT_ZIPY_KEY = '53a1f38c';
const DEFAULT_USERSNAP_KEY = '41299298-9c0f-4c23-951b-2f61d7cd25a1';

/**
 * Get analytics configuration from environment
 */
export const getAnalyticsConfig = () => {
  const envConfig = window.ENV_CONFIG || {};
  
  // Priority: ENV_CONFIG > VITE env > Default
  const zipyKey = envConfig.ZIPY_PROJECT_KEY || import.meta.env.VITE_ZIPY_PROJECT_KEY || DEFAULT_ZIPY_KEY;
  const usersnapKey = envConfig.USERSNAP_PROJECT_KEY || import.meta.env.VITE_USERSNAP_PROJECT_KEY || DEFAULT_USERSNAP_KEY;
  
  return {
    zipy: {
      projectKey: zipyKey,
      enabled: !!zipyKey,
    },
    usersnap: {
      projectKey: usersnapKey,
      enabled: !!usersnapKey,
    },
  };
};

/**
 * Check if we're in production environment
 */
export const isProduction = () => {
  return import.meta.env.PROD || 
         (window.location.hostname !== 'localhost' && 
          window.location.hostname !== '127.0.0.1');
};

