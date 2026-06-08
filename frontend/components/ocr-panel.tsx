'use client';

import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import { FieldInput } from '@/components/field-input';
import { SectionShell } from '@/components/section-shell';
import { StatusOverview } from '@/components/status-overview';
import { ocrApiClient } from '@/lib/api-client';
import { useOCRStore } from '@/lib/ocr-store';
import { useOCRWebSocket } from '@/lib/use-ocr-websocket';

type Language = 'vi' | 'en';

const translations = {
  vi: {
    panel: 'OCR Panel',
    status: 'Trạng thái',
    retry: 'Kiểm tra lại',
    checking: 'Đang kiểm tra...',
    model: 'Model',
    path: 'Đường dẫn',
    loadModel: 'Nạp model',
    loading: 'Đang nạp...',
    config: 'Cấu hình',
    acceptance: 'Acceptance',
    duplication: 'Duplication',
    row: 'Row',
    input: 'Ảnh vào',
    selectImage: 'Chọn ảnh',
    processing: 'Đang xử lý...',
    preview: 'Xem trước',
    result: 'Kết quả',
    noResult: 'Chưa có kết quả',
    api: 'API',
    socket: 'Socket',
    synced: 'Đã đồng bộ',
    pending: 'Chờ đồng bộ',
    online: 'Online',
    offline: 'Offline',
    loaded: 'Đã nạp',
    required: 'Cần nạp',
    ready: 'Sẵn sàng',
    waiting: 'Đang chờ',
    language: 'Ngôn ngữ',
    backend: 'Backend',
    localModelPath: 'Đường dẫn model local',
    acceptanceTooltip: 'Ngưỡng chấp nhận',
    duplicationTooltip: 'Ngưỡng trùng lặp',
    rowTooltip: 'Ngưỡng dòng',
    retryTooltip: 'Kiểm tra kết nối backend',
    selectImageTooltip: 'Chọn ảnh gửi OCR',
    loadModelTooltip: 'Nạp model OCR',
    loadPathFirst: 'Nhập đường dẫn model trước khi nạp.',
    backendChecking: 'Đang kiểm tra backend...',
    backendOffline: 'Backend vẫn đang offline.',
    backendRestored: 'Đã kết nối lại backend.',
    cannotConnect: 'Không thể kết nối OCR API tại http://localhost:8000. Hãy mở backend và thử lại.',
    needModel: 'Cần nạp model OCR trước khi gửi ảnh.',
    socketNotReady: 'Socket chưa sẵn sàng. Thử lại sau.',
    canvasUnavailable: 'Không tạo được canvas.',
    prepareImageFailed: 'Không thể chuẩn bị ảnh để OCR.',
    sendingImage: 'Đang gửi ảnh lên backend...',
    loadingModel: 'Đang nạp model OCR...',
    loadModelSuccess: 'Nạp model OCR thành công.',
    loadModelFailed: 'Nạp model OCR thất bại.',
    configSyncedToast: 'Đã đồng bộ cấu hình OCR.',
    ocrCompleted: 'OCR hoàn tất.',
    ocrError: 'OCR trả về lỗi.',
  },
  en: {
    panel: 'OCR Panel',
    status: 'Status',
    retry: 'Retry',
    checking: 'Checking...',
    model: 'Model',
    path: 'Path',
    loadModel: 'Load Model',
    loading: 'Loading...',
    config: 'Config',
    acceptance: 'Acceptance',
    duplication: 'Duplication',
    row: 'Row',
    input: 'Input',
    selectImage: 'Select Image',
    processing: 'Processing...',
    preview: 'Preview',
    result: 'Result',
    noResult: 'No result',
    api: 'API',
    socket: 'Socket',
    synced: 'Synced',
    pending: 'Pending',
    online: 'Online',
    offline: 'Offline',
    loaded: 'Loaded',
    required: 'Required',
    ready: 'Ready',
    waiting: 'Waiting',
    language: 'Language',
    backend: 'Backend',
    localModelPath: 'Local model path',
    acceptanceTooltip: 'Acceptance threshold',
    duplicationTooltip: 'Duplication threshold',
    rowTooltip: 'Row threshold',
    retryTooltip: 'Check backend connection again',
    selectImageTooltip: 'Choose an image for OCR',
    loadModelTooltip: 'Load OCR model',
    loadPathFirst: 'Enter a model path before loading.',
    backendChecking: 'Checking backend...',
    backendOffline: 'Backend is still offline.',
    backendRestored: 'Backend connection restored.',
    cannotConnect: 'Cannot connect to OCR API at http://localhost:8000. Please start the backend and retry.',
    needModel: 'Load an OCR model before sending images.',
    socketNotReady: 'WebSocket is not ready yet. Retry shortly.',
    canvasUnavailable: 'Canvas context is unavailable.',
    prepareImageFailed: 'Failed to prepare the image for OCR.',
    sendingImage: 'Sending image to backend...',
    loadingModel: 'Loading OCR model...',
    loadModelSuccess: 'OCR model loaded successfully.',
    loadModelFailed: 'Failed to load OCR model.',
    configSyncedToast: 'OCR configuration synced.',
    ocrCompleted: 'OCR completed.',
    ocrError: 'OCR returned an error.',
  },
} as const;

export function OCRPanel() {
  const modelPath = useOCRStore((state) => state.modelPath);
  const config = useOCRStore((state) => state.config);
  const setConnected = useOCRStore((state) => state.setConnected);
  const setError = useOCRStore((state) => state.setError);
  const setProcessing = useOCRStore((state) => state.setProcessing);
  const setModelPath = useOCRStore((state) => state.setModelPath);
  const setConfig = useOCRStore((state) => state.setConfig);
  const [language, setLanguage] = useState<Language>('vi');
  const [apiConnected, setApiConnected] = useState(false);
  const [isCheckingApi, setIsCheckingApi] = useState(true);
  const [configSynced, setConfigSynced] = useState(false);
  const [localModelPath, setLocalModelPath] = useState('');
  const {
    isConnected: wsConnected,
    sendImage,
    lastResult,
    isProcessing,
    error,
  } = useOCRWebSocket(apiConnected);

  const t = translations[language];
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const savedLanguage = window.localStorage.getItem('ocr-panel-language');
    if (savedLanguage === 'vi' || savedLanguage === 'en') {
      setLanguage(savedLanguage);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem('ocr-panel-language', language);
  }, [language]);

  useEffect(() => {
    let isMounted = true;

    const checkConnection = async () => {
      setIsCheckingApi(true);

      const result = await ocrApiClient.healthCheck();
      if (!isMounted) {
        return;
      }

      setApiConnected(result.success);
      setConnected(result.success);

      if (!result.success) {
        setConfigSynced(false);
        setError(t.cannotConnect);
      } else {
        setError(null);
      }

      setIsCheckingApi(false);
    };

    checkConnection();

    return () => {
      isMounted = false;
    };
  }, [setConnected, setError, t.cannotConnect]);

  useEffect(() => {
    setLocalModelPath(modelPath ?? '');
  }, [modelPath]);

  useEffect(() => {
    if (!apiConnected) {
      return;
    }

    let cancelled = false;

    const syncConfig = async () => {
      const response = await ocrApiClient.setConfig(config);
      if (cancelled) {
        return;
      }

      if (response.success) {
        setConfigSynced(true);
      } else {
        setConfigSynced(false);
        setError(response.error || t.loadModelFailed);
      }
    };

    syncConfig();

    return () => {
      cancelled = true;
    };
  }, [apiConnected, config, setError, t.loadModelFailed]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleRetryConnection = async () => {
    setIsCheckingApi(true);
    toast.loading(t.backendChecking, { id: 'backend-check' });

    const result = await ocrApiClient.healthCheck();
    setApiConnected(result.success);
    setConnected(result.success);

    if (!result.success) {
      setConfigSynced(false);
      setError(t.cannotConnect);
      toast.error(t.backendOffline, { id: 'backend-check' });
    } else {
      setError(null);
      toast.success(t.backendRestored, { id: 'backend-check' });
    }

    setIsCheckingApi(false);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!modelPath) {
      setError(t.needModel);
      toast.warning(t.needModel);
      event.target.value = '';
      return;
    }

    if (!wsConnected) {
      setError(t.socketNotReady);
      toast.warning(t.socketNotReady);
      event.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = (loadEvent) => {
      const img = new Image();
      img.onload = () => {
        if (!canvasRef.current) {
          return;
        }

        const ctx = canvasRef.current.getContext('2d');
        if (!ctx) {
          toast.error(t.canvasUnavailable);
          return;
        }

        canvasRef.current.width = img.width;
        canvasRef.current.height = img.height;
        ctx.drawImage(img, 0, 0);

        canvasRef.current.toBlob((blob) => {
          if (!blob) {
            toast.error(t.prepareImageFailed);
            return;
          }

          if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
          }

          const nextPreviewUrl = URL.createObjectURL(blob);
          setPreviewUrl(nextPreviewUrl);
          toast.loading(t.sendingImage, { id: 'ocr-upload' });
          sendImage(blob);
        }, 'image/jpeg');
      };

      img.src = loadEvent.target?.result as string;
    };

    reader.readAsDataURL(file);
  };

  const handleLoadModel = async () => {
    if (!localModelPath.trim()) {
      toast.warning(t.loadPathFirst);
      return;
    }

    setProcessing(true);
    toast.loading(t.loadingModel, { id: 'model-load' });
    const response = await ocrApiClient.loadModel(localModelPath.trim());

    if (response.success) {
      setModelPath(localModelPath.trim());
      setError(null);
      toast.success(t.loadModelSuccess, { id: 'model-load' });
    } else {
      setError(response.error || t.loadModelFailed);
      toast.error(response.error || t.loadModelFailed, { id: 'model-load' });
    }

    setProcessing(false);
  };

  const handleConfigChange = async (
    key: 'acceptance_threshold_ocr' | 'duplication_threshold_ocr' | 'row_threshold',
    rawValue: number
  ) => {
    const nextConfig = { ...config, [key]: rawValue };
    setConfigSynced(false);
    await setConfig(nextConfig);
    setConfigSynced(true);
    toast.success(t.configSyncedToast);
  };

  useEffect(() => {
    if (!lastResult) {
      return;
    }

    toast.success(lastResult.success ? t.ocrCompleted : t.ocrError, {
      id: 'ocr-upload',
    });
  }, [lastResult, t.ocrCompleted, t.ocrError]);

  useEffect(() => {
    if (!error) {
      return;
    }

    toast.error(error, { id: 'ocr-error' });
  }, [error]);

  return (
    <div className="w-full max-w-7xl space-y-6">
      <section className="rounded-[28px] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-6 shadow-[0_20px_60px_rgba(17,24,39,0.08)] md:px-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="flex items-center gap-3">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[color:var(--muted-strong)]">
              {t.panel}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-[color:var(--border-soft)] bg-[color:var(--surface-soft)] p-1">
              <span className="px-3 text-xs font-medium text-[color:var(--muted)]">
                {t.language}
              </span>
              <button
                onClick={() => setLanguage('vi')}
                className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                  language === 'vi'
                    ? 'bg-[color:var(--foreground)] text-[color:var(--background)]'
                    : 'text-[color:var(--muted-strong)]'
                }`}
                title="Tiếng Việt"
              >
                VI
              </button>
              <button
                onClick={() => setLanguage('en')}
                className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                  language === 'en'
                    ? 'bg-[color:var(--foreground)] text-[color:var(--background)]'
                    : 'text-[color:var(--muted-strong)]'
                }`}
                title="English"
              >
                EN
              </button>
            </div>

            <button
              onClick={handleRetryConnection}
              disabled={isCheckingApi}
              title={t.retryTooltip}
              className="rounded-full border border-[color:var(--border-strong)] px-4 py-2 text-sm font-medium text-[color:var(--foreground)] transition hover:bg-[color:var(--surface-muted)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isCheckingApi ? t.checking : t.retry}
            </button>
          </div>
        </div>

        <div className="mt-5">
          <StatusOverview
            apiConnected={apiConnected}
            isCheckingApi={isCheckingApi}
            wsConnected={wsConnected}
            modelReady={Boolean(modelPath)}
            configSynced={configSynced}
            labels={{
              api: t.api,
              config: t.config,
              model: t.model,
              socket: t.socket,
              checking: t.checking,
              online: t.online,
              offline: t.offline,
              synced: t.synced,
              pending: t.pending,
              loaded: t.loaded,
              required: t.required,
              ready: t.ready,
              waiting: t.waiting,
            }}
          />
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-6">
          <SectionShell title={t.model} tone={!apiConnected ? 'warning' : 'default'}>
            <div className="space-y-4">
              <FieldInput
                label={t.path}
                value={localModelPath}
                onChange={(event) => setLocalModelPath(event.target.value)}
                placeholder="C:\\Models\\ocr_model.pt"
                disabled={!apiConnected || isProcessing}
                hint={modelPath ? `${t.loaded}: ${modelPath}` : undefined}
                tooltip={t.localModelPath}
              />
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={handleLoadModel}
                  disabled={!apiConnected || isProcessing}
                  title={t.loadModelTooltip}
                  className="rounded-full bg-[color:var(--accent)] px-5 py-2.5 text-sm font-semibold text-[color:var(--accent-foreground)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isProcessing ? t.loading : t.loadModel}
                </button>
              </div>
            </div>
          </SectionShell>

          <SectionShell title={t.config}>
            <div className="grid gap-4 md:grid-cols-3">
              <FieldInput
                label={t.acceptance}
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={config.acceptance_threshold_ocr}
                disabled={!apiConnected}
                tooltip={t.acceptanceTooltip}
                onChange={(event) =>
                  handleConfigChange('acceptance_threshold_ocr', Number(event.target.value))
                }
              />
              <FieldInput
                label={t.duplication}
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={config.duplication_threshold_ocr}
                disabled={!apiConnected}
                tooltip={t.duplicationTooltip}
                onChange={(event) =>
                  handleConfigChange('duplication_threshold_ocr', Number(event.target.value))
                }
              />
              <FieldInput
                label={t.row}
                type="number"
                min="0"
                step="1"
                value={config.row_threshold}
                disabled={!apiConnected}
                tooltip={t.rowTooltip}
                onChange={(event) =>
                  handleConfigChange('row_threshold', Number(event.target.value))
                }
              />
            </div>
          </SectionShell>

          <SectionShell
            title={t.input}
            action={
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={!wsConnected || !modelPath || isProcessing}
                title={t.selectImageTooltip}
                className="rounded-full bg-[color:var(--foreground)] px-5 py-2.5 text-sm font-semibold text-[color:var(--background)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isProcessing ? t.processing : t.selectImage}
              </button>
            }
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
            <div className="grid gap-3 text-sm text-[color:var(--muted)] md:grid-cols-3">
              <div className="rounded-2xl bg-[color:var(--surface-soft)] p-4">
                <p className="font-medium text-[color:var(--foreground)]">{t.backend}</p>
                <p className="mt-1">{apiConnected ? t.online : t.offline}</p>
              </div>
              <div className="rounded-2xl bg-[color:var(--surface-soft)] p-4">
                <p className="font-medium text-[color:var(--foreground)]">{t.model}</p>
                <p className="mt-1">{modelPath ? t.loaded : t.required}</p>
              </div>
              <div className="rounded-2xl bg-[color:var(--surface-soft)] p-4">
                <p className="font-medium text-[color:var(--foreground)]">{t.socket}</p>
                <p className="mt-1">{wsConnected ? t.ready : t.waiting}</p>
              </div>
            </div>
          </SectionShell>
        </div>

        <div className="space-y-6">
          <SectionShell title={t.preview}>
            <div className="rounded-3xl border border-dashed border-[color:var(--border-strong)] bg-[color:var(--surface-soft)] p-4">
              <canvas
                ref={canvasRef}
                className="max-h-[420px] w-full rounded-2xl bg-[color:var(--surface)] object-contain"
              />
            </div>
          </SectionShell>

          <SectionShell title={t.result}>
            <div className="rounded-3xl border border-[color:var(--border-soft)] bg-[color:var(--surface-soft)] p-4">
              {lastResult ? (
                <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-words text-sm leading-6 text-[color:var(--foreground)]">
                  {JSON.stringify(lastResult, null, 2)}
                </pre>
              ) : (
                <p className="text-sm text-[color:var(--muted)]">{t.noResult}</p>
              )}
            </div>
          </SectionShell>
        </div>
      </div>
    </div>
  );
}
