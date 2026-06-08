import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const API_ROOT_URL =
  process.env.NEXT_PUBLIC_API_ROOT_URL || 'http://localhost:8000';

/**
 * OCR API Response Types
 */
export interface OCRResponse {
  success: boolean;
  message?: string;
  error?: string;
  data?: any;
}

/**
 * OCR Configuration
 */
export interface OCRConfig {
  acceptance_threshold_ocr: number;
  duplication_threshold_ocr: number;
  row_threshold: number;
}

export interface HealthCheckResult {
  success: boolean;
  error?: string;
}

/**
 * API Client for OCR AI service
 */
class OCRApiClient {
  private client: AxiosInstance;
  private rootClient: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.rootClient = axios.create({
      baseURL: API_ROOT_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Health check - verify API is running
   */
  async healthCheck(): Promise<HealthCheckResult> {
    try {
      const response = await this.rootClient.get('/');
      return {
        success: response.status === 200,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error?.message || 'Failed to connect to OCR API',
      };
    }
  }

  /**
   * Load OCR model from file path
   */
  async loadModel(modelPath: string): Promise<OCRResponse> {
    try {
      const response = await this.client.post('/ai/ocr_ai/load_model', null, {
        params: { model_path: modelPath },
      });
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to load model',
      };
    }
  }

  /**
   * Configure OCR parameters
   */
  async setConfig(config: Partial<OCRConfig>): Promise<OCRResponse> {
    try {
      const response = await this.client.post('/ai/ocr_ai/input_config', null, {
        params: {
          acceptance_threshold_ocr: config.acceptance_threshold_ocr ?? 0.5,
          duplication_threshold_ocr: config.duplication_threshold_ocr ?? 0.5,
          row_threshold: config.row_threshold ?? 20,
        },
      });
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to set config',
      };
    }
  }

  /**
   * Get WebSocket URL for real-time OCR
   */
  getWebSocketUrl(): string {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    return `${wsUrl}/ai/ocr_ai/ws`;
  }
}

export const ocrApiClient = new OCRApiClient();
