// API Configuration
export const getApiBaseUrl = () => {
	// First priority: ENV_CONFIG from /env-config endpoint
	if (window.ENV_CONFIG && window.ENV_CONFIG.AGENTHUB_MAIN_DOMAIN) {
		return window.ENV_CONFIG.AGENTHUB_MAIN_DOMAIN;
	}

	// Second priority: Global window variable
	if (window.AGENTHUB_MAIN_DOMAIN) {
		return window.AGENTHUB_MAIN_DOMAIN;
	}

	// Third priority: Build-time environment variable (Vite uses import.meta.env)
	if (import.meta.env.VITE_AGENTHUB_MAIN_DOMAIN) {
		return import.meta.env.VITE_AGENTHUB_MAIN_DOMAIN;
	}

	// Fallback: If we're on a deployed site (not localhost), use same origin
	// This handles cases where /env-config hasn't loaded yet or is missing
	const hostname = window.location.hostname;
	if (hostname !== 'localhost' && hostname !== '127.0.0.1' && hostname !== '0.0.0.0') {
		return window.location.origin;
	}

	// Local development: Return empty string so relative URLs work with Vite proxy
	return '';
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
