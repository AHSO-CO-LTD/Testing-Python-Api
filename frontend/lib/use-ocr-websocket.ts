import { useEffect, useRef, useCallback } from 'react';
import { ocrApiClient } from './api-client';
import { useOCRStore } from './ocr-store';

/**
 * Hook to manage WebSocket connection for real-time OCR
 */
export const useOCRWebSocket = (enabled: boolean) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldReconnectRef = useRef(true);
  const wsConnected = useOCRStore((state) => state.wsConnected);
  const lastResult = useOCRStore((state) => state.lastResult);
  const isProcessing = useOCRStore((state) => state.isProcessing);
  const error = useOCRStore((state) => state.error);
  const setWSConnected = useOCRStore((state) => state.setWSConnected);
  const setLastResult = useOCRStore((state) => state.setLastResult);
  const setError = useOCRStore((state) => state.setError);
  const setProcessing = useOCRStore((state) => state.setProcessing);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = useRef(1000);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!enabled) {
      return;
    }

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const wsUrl = ocrApiClient.getWebSocketUrl();
      console.log('[OCR WebSocket] Connecting to:', wsUrl);

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[OCR WebSocket] Connected');
        setWSConnected(true);
        reconnectAttempts.current = 0;
        reconnectDelay.current = 1000;
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const result = JSON.parse(event.data);
          setLastResult(result);
          setError(null);
        } catch (error) {
          console.error('[OCR WebSocket] Parse error:', error);
        }
      };

      ws.onerror = (error: Event) => {
        console.error('[OCR WebSocket] Error:', error);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('[OCR WebSocket] Disconnected');
        setWSConnected(false);
        wsRef.current = null;

        // Attempt to reconnect
        if (shouldReconnectRef.current && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          console.log(
            `[OCR WebSocket] Reconnecting... (${reconnectAttempts.current}/${maxReconnectAttempts})`
          );
          reconnectTimeoutRef.current = setTimeout(connect, reconnectDelay.current);
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 10000);
        } else if (shouldReconnectRef.current) {
          setError('WebSocket connection failed after multiple attempts');
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[OCR WebSocket] Connection error:', error);
      setError(String(error));
    }
  }, [enabled, setError, setLastResult, setWSConnected]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      console.log('[OCR WebSocket] Closing connection');
      wsRef.current.close();
      wsRef.current = null;
    }

    reconnectAttempts.current = 0;
    reconnectDelay.current = 1000;
    setWSConnected(false);
  }, [setWSConnected]);

  /**
   * Send image data to WebSocket (as binary)
   */
  const sendImage = useCallback(
    (imageData: Blob | ArrayBuffer) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError('WebSocket not connected');
        return;
      }

      try {
        setProcessing(true);
        wsRef.current.send(imageData);
      } catch (error) {
        console.error('[OCR WebSocket] Send error:', error);
        setError(String(error));
      } finally {
        setProcessing(false);
      }
    },
    [setError, setProcessing]
  );

  /**
   * Auto-connect on mount, disconnect on unmount
   */
  useEffect(() => {
    shouldReconnectRef.current = enabled;

    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect, enabled]);

  return {
    isConnected: wsConnected,
    sendImage,
    connect,
    disconnect,
    lastResult,
    isProcessing,
    error,
  };
};
