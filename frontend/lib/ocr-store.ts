import { create } from 'zustand';
import { ocrApiClient, OCRConfig } from './api-client';

/**
 * OCR Store State
 */
export interface OCRStore {
  // State
  isConnected: boolean;
  isProcessing: boolean;
  modelPath: string | null;
  config: OCRConfig;
  wsConnected: boolean;
  lastResult: any | null;
  error: string | null;

  // Actions
  setConnected: (connected: boolean) => void;
  setProcessing: (processing: boolean) => void;
  setModelPath: (path: string) => void;
  setConfig: (config: Partial<OCRConfig>) => Promise<void>;
  setWSConnected: (connected: boolean) => void;
  setLastResult: (result: any) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

/**
 * Initial config state
 */
const initialConfig: OCRConfig = {
  acceptance_threshold_ocr: 0.5,
  duplication_threshold_ocr: 0.5,
  row_threshold: 20,
};

/**
 * Zustand store for OCR state
 */
export const useOCRStore = create<OCRStore>((set) => ({
  // Initial state
  isConnected: false,
  isProcessing: false,
  modelPath: null,
  config: initialConfig,
  wsConnected: false,
  lastResult: null,
  error: null,

  // Actions
  setConnected: (connected: boolean) => set({ isConnected: connected }),
  setProcessing: (processing: boolean) => set({ isProcessing: processing }),
  setModelPath: (path: string) => set({ modelPath: path }),

  setConfig: async (config: Partial<OCRConfig>) => {
    const response = await ocrApiClient.setConfig(config);
    if (response.success) {
      set((state) => ({
        config: { ...state.config, ...config },
        error: null,
      }));
    } else {
      set({ error: response.error || 'Failed to set config' });
    }
  },

  setWSConnected: (connected: boolean) => set({ wsConnected: connected }),
  setLastResult: (result: any) => set({ lastResult: result }),
  setError: (error: string | null) => set({ error }),

  reset: () =>
    set({
      isConnected: false,
      isProcessing: false,
      modelPath: null,
      config: initialConfig,
      wsConnected: false,
      lastResult: null,
      error: null,
    }),
}));
