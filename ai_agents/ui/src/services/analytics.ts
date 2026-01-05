/**
 * Analytics Service
 * 
 * Handles initialization and user identification for:
 * - Zipy.ai: Session recording and error monitoring
 * - Usersnap: Bug reporting and user feedback
 */

import { getAnalyticsConfig, isProduction } from '../config/analytics';

// Declare global types for analytics SDKs
declare global {
  interface Window {
    zipy?: {
      init: (projectKey: string) => void;
      identify: (userId: string, userInfo: Record<string, string>) => void;
      getCurrentSessionURL: () => string | null;
    };
    Usersnap?: {
      init: (config: { apiKey: string; email?: string; custom?: Record<string, unknown> }) => void;
      on: (event: string, callback: (data: unknown) => void) => void;
      show: (projectKey: string) => void;
      hide: () => void;
    };
    onUsersnapCXLoad?: (api: typeof window.Usersnap) => void;
  }
}

interface UserInfo {
  id: string;
  email: string;
  name: string;
}

let isInitialized = false;
let currentUser: UserInfo | null = null;

/**
 * Load Zipy SDK dynamically
 */
const loadZipy = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (window.zipy) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://cdn.zipy.ai/sdk/v1.0/zipy.min.umd.js';
    script.async = true;
    script.crossOrigin = 'anonymous';
    
    script.onload = () => {
      console.log('✅ Zipy SDK loaded');
      resolve();
    };
    
    script.onerror = () => {
      console.warn('⚠️ Failed to load Zipy SDK');
      reject(new Error('Failed to load Zipy SDK'));
    };
    
    document.head.appendChild(script);
  });
};

/**
 * Load Usersnap SDK dynamically
 */
const loadUsersnap = (projectKey: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (window.Usersnap) {
      resolve();
      return;
    }

    // Set up callback before loading script
    window.onUsersnapCXLoad = (api) => {
      window.Usersnap = api;
      console.log('✅ Usersnap SDK loaded');
      resolve();
    };

    const script = document.createElement('script');
    script.src = `https://widget.usersnap.com/global/load/${projectKey}?onload=onUsersnapCXLoad`;
    script.async = true;
    
    script.onerror = () => {
      console.warn('⚠️ Failed to load Usersnap SDK');
      reject(new Error('Failed to load Usersnap SDK'));
    };
    
    document.head.appendChild(script);
  });
};

/**
 * Initialize Zipy session recording
 */
const initZipy = async (projectKey: string): Promise<void> => {
  try {
    await loadZipy();
    
    if (window.zipy) {
      window.zipy.init(projectKey);
      console.log('✅ Zipy initialized');
      
      // If we have a user, identify them
      if (currentUser) {
        identifyUserInZipy(currentUser);
      }
    }
  } catch (error) {
    console.warn('Failed to initialize Zipy:', error);
  }
};

/**
 * Initialize Usersnap feedback widget
 */
const initUsersnap = async (projectKey: string): Promise<void> => {
  try {
    await loadUsersnap(projectKey);
    
    if (window.Usersnap) {
      // Initialize with user info if available
      const initConfig: { apiKey: string; email?: string; custom?: Record<string, unknown> } = {
        apiKey: projectKey,
      };
      
      if (currentUser) {
        initConfig.email = currentUser.email;
        initConfig.custom = {
          userId: currentUser.id,
          userName: currentUser.name,
        };
      }
      
      window.Usersnap.init(initConfig);
      console.log('✅ Usersnap initialized');
    }
  } catch (error) {
    console.warn('Failed to initialize Usersnap:', error);
  }
};

/**
 * Identify user in Zipy
 */
const identifyUserInZipy = (user: UserInfo): void => {
  if (window.zipy) {
    window.zipy.identify(user.id, {
      email: user.email,
      name: user.name,
    });
    console.log('✅ User identified in Zipy:', user.email);
  }
};

/**
 * Initialize all analytics services
 */
export const initAnalytics = async (): Promise<void> => {
  if (isInitialized) {
    console.log('Analytics already initialized');
    return;
  }

  const config = getAnalyticsConfig();
  const shouldInit = isProduction() || import.meta.env.DEV; // Init in both prod and dev for testing

  console.log('🔧 Analytics config:', {
    zipy: { enabled: config.zipy.enabled, hasKey: !!config.zipy.projectKey },
    usersnap: { enabled: config.usersnap.enabled, hasKey: !!config.usersnap.projectKey },
    environment: isProduction() ? 'production' : 'development',
  });

  if (!shouldInit) {
    console.log('Analytics disabled in this environment');
    return;
  }

  const initPromises: Promise<void>[] = [];

  // Initialize Zipy
  if (config.zipy.enabled && config.zipy.projectKey) {
    initPromises.push(initZipy(config.zipy.projectKey));
  } else {
    console.log('ℹ️ Zipy not configured (set VITE_ZIPY_PROJECT_KEY or ZIPY_PROJECT_KEY in env-config)');
  }

  // Initialize Usersnap
  if (config.usersnap.enabled && config.usersnap.projectKey) {
    initPromises.push(initUsersnap(config.usersnap.projectKey));
  } else {
    console.log('ℹ️ Usersnap not configured (set VITE_USERSNAP_PROJECT_KEY or USERSNAP_PROJECT_KEY in env-config)');
  }

  await Promise.allSettled(initPromises);
  isInitialized = true;
  console.log('✅ Analytics initialization complete');
};

/**
 * Identify the current user for analytics
 * Call this after user logs in
 */
export const identifyUser = (user: UserInfo): void => {
  currentUser = user;
  
  // Update Zipy
  identifyUserInZipy(user);
  
  // Update Usersnap (re-init with user info)
  const config = getAnalyticsConfig();
  if (config.usersnap.enabled && window.Usersnap) {
    window.Usersnap.init({
      apiKey: config.usersnap.projectKey,
      email: user.email,
      custom: {
        userId: user.id,
        userName: user.name,
      },
    });
  }
  
  console.log('✅ User identified in analytics:', user.email);
};

/**
 * Clear user identity (on logout)
 */
export const clearUserIdentity = (): void => {
  currentUser = null;
  console.log('✅ User identity cleared from analytics');
};

/**
 * Get current Zipy session URL
 * Useful for including in bug reports
 */
export const getSessionReplayURL = (): string | null => {
  if (window.zipy) {
    return window.zipy.getCurrentSessionURL();
  }
  return null;
};

/**
 * Show Usersnap feedback widget programmatically
 */
export const showFeedbackWidget = (): void => {
  const config = getAnalyticsConfig();
  if (window.Usersnap && config.usersnap.projectKey) {
    window.Usersnap.show(config.usersnap.projectKey);
  } else {
    console.warn('Usersnap not initialized');
  }
};

/**
 * Hide Usersnap feedback widget
 */
export const hideFeedbackWidget = (): void => {
  if (window.Usersnap) {
    window.Usersnap.hide();
  }
};

export default {
  initAnalytics,
  identifyUser,
  clearUserIdentity,
  getSessionReplayURL,
  showFeedbackWidget,
  hideFeedbackWidget,
};

