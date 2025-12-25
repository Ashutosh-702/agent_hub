// API Configuration
export const getApiBaseUrl = () => {
	if (window.ENV_CONFIG && window.ENV_CONFIG.AGENTHUB_MAIN_DOMAIN) {
		return window.ENV_CONFIG.AGENTHUB_MAIN_DOMAIN;
	}

	if (window.AGENTHUB_MAIN_DOMAIN) {
		return window.AGENTHUB_MAIN_DOMAIN;
	}

	// Frontend + backend are the same domain (SIT/Prod): default to current origin.
	// This avoids Mixed Content when the page is HTTPS and /env-config is slow.
	if (window.location && window.location.origin) {
		return window.location.origin;
	}

	return process.env.AGENTHUB_MAIN_DOMAIN || 'http://0.0.0.0:80';
};

export const initializeConfig = async () => {
	return {
		api_base_url: getApiBaseUrl(),
		environment: window.ENV_CONFIG?.ENVIRONMENT || 'development',
		version: window.ENV_CONFIG?.VERSION || '2.0.0',
	};
};

export const API_BASE_URL = getApiBaseUrl();
export const API_URL = `${getApiBaseUrl()}/api`;

export const getConfig = () => window.ENV_CONFIG || null;
