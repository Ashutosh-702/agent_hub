import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { API_BASE_URL } from '../../config/api.js';

// Base API with common configuration
export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers) => {
      headers.set('accept', 'application/json');
      // Do NOT force Content-Type globally.
      // Some endpoints (e.g. PATCH with only query params) have no body and may reject an explicit JSON Content-Type.
      // fetchBaseQuery will automatically set application/json when a JSON body is present.
      return headers;
    },
  }),
  tagTypes: ['Campaign', 'Company', 'Contact'],
  endpoints: () => ({}),
});

