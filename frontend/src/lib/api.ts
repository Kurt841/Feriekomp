import axios from 'axios';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { BeregnInput, BeregnOutput, BesokOutput } from './validation';

// API base URL-konfigurasjon
// Produksjon: Sett NEXT_PUBLIC_API_BASE_URL i .env til din offentlige backend-URL
// (f.eks. https://api.feriekomp.example.com eller /api hvis bak samme domene)
const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:5000';
  }
  return '/api';
};

const API_BASE_URL = getApiBaseUrl();
const api = axios.create({
  baseURL: API_BASE_URL || undefined,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`Gjør ${config.method?.toUpperCase()} forespørsel til ${config.url}`);
    }
    return config;
  },
  (feil) => {
    if (process.env.NODE_ENV === 'development') {
      console.error('Forespørselsfeil:', feil);
    }
    return Promise.reject(feil);
  }
);

api.interceptors.response.use(
  (response) => response,
  (feil) => {
    if (process.env.NODE_ENV === 'development') {
      if (feil.code === 'ECONNABORTED') {
        console.error('API-feil: Timeout - backend svarer ikke innen 30 sekunder');
      } else if (feil.code === 'ECONNRESET' || feil.message?.includes('socket hang up')) {
        console.error('API-feil: Tilkobling til backend ble avbrutt. Sjekk at backend kjører på port 5000');
      } else if (feil.response) {
        console.error('API-feil:', feil.response.status, feil.response.data || feil.message);
      } else {
        console.error('API-feil:', feil.message || feil);
      }
    }
    return Promise.reject(feil);
  }
);

export const registrerBesok = async (): Promise<BesokOutput | null> => {
  try {
    const response = await api.post<BesokOutput>('/besok', {});
    return response.data;
  } catch (feil) {
    if (process.env.NODE_ENV === 'development') {
      console.warn('Besøksregistrering feilet (ignoreres):', feil);
    }
    return null;
  }
};

export const beregnKompensasjon = async (data: BeregnInput): Promise<BeregnOutput> => {
  try {
    const response = await api.post<BeregnOutput>('/beregn', data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const detail = error.response.data?.detail;
        if (typeof detail === 'string') {
          throw new Error(detail);
        } else if (detail?.error) {
          throw new Error(detail.error);
        } else if (detail?.message) {
          throw new Error(detail.message);
        }
        throw new Error(`Beregning feilet: ${error.response.status} ${error.response.statusText}`);
      } else if (error.request) {
        throw new Error('Kunne ikke koble til serveren. Sjekk at backend kjører.');
      }
    }
    throw error instanceof Error ? error : new Error('En ukjent feil oppstod');
  }
};

export const forklarBeregning = async (input: BeregnInput, resultat?: BeregnOutput) => {
  try {
    const body = { input, ...(resultat && { resultat }) };
    const response = await api.post<{ forklaring: string; resultat: BeregnOutput }>('/forklar', body);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const detail = error.response.data?.detail;
        if (typeof detail === 'string') {
          throw new Error(detail);
        } else if (detail?.error) {
          throw new Error(detail.error);
        }
        throw new Error(`Kunne ikke generere forklaring: ${error.response.status}`);
      } else if (error.request) {
        throw new Error('Kunne ikke koble til serveren. Sjekk at backend kjører.');
      }
    }
    throw error instanceof Error ? error : new Error('En ukjent feil oppstod');
  }
};

export const useRegistrerBesok = () => {
  return useQuery({
    queryKey: ['besok'],
    queryFn: registrerBesok,
    staleTime: Infinity,
    retry: false,
  });
};

export const useBeregnKompensasjon = () => {
  return useMutation({
    mutationFn: beregnKompensasjon,
  });
};

export const useForklarBeregning = () => {
  return useMutation({
    mutationFn: ({ input, resultat }: { input: BeregnInput; resultat?: BeregnOutput }) =>
      forklarBeregning(input, resultat),
  });
};

export default api;
