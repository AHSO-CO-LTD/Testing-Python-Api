# VisionCenter OCR - Frontend Migration Guide

## 📋 Overview
Successfully migrated from PyQt5 desktop app to modern **Next.js + Electron** stack with **TypeScript** and **Tailwind CSS**.

## 🎯 Current Status
✅ **PHASE 1 COMPLETE:** OCR UI frontend with real-time WebSocket support

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.11 (for backend - NOT 3.14 due to package incompatibilities)
- npm or yarn

### Backend Setup (Python)
```bash
# Install dependencies (use Python 3.11)
pip install -r requirements.txt

# Start API server
python main.py
# Server runs on http://localhost:8000
# API docs: http://localhost:8000/api/docs
```

### Frontend Setup (Node.js)
```bash
cd frontend

# Install dependencies
npm install

# Development mode
npm run dev
# Open http://localhost:3000

# With Electron (desktop)
npm run electron-dev

# Production build
npm run electron-build
# Output: frontend/dist/VisionCenter-OCR-Setup-1.0.0.exe
```

## 📁 Project Structure

```
Testing-Python-Api/
├── main.py                          # Backend entry point
├── requirements.txt                 # Python dependencies
├── config.json                      # API configuration
│
├── api/                             # FastAPI application
│   ├── app.py                      # FastAPI setup
│   ├── routers/
│   │   └── OCR_AI_router.py        # OCR endpoints
│   └── backend/AI/                 # AI logic
│
├── frontend/                        # Next.js + Electron app
│   ├── app/
│   │   ├── page.tsx               # Home page
│   │   ├── layout.tsx             # Root layout
│   │   └── globals.css            # Global styles
│   │
│   ├── components/
│   │   └── ocr-panel.tsx          # Main OCR UI
│   │
│   ├── lib/
│   │   ├── api-client.ts          # HTTP API client
│   │   ├── ocr-store.ts           # Zustand state
│   │   └── use-ocr-websocket.ts   # WebSocket hook
│   │
│   ├── public/
│   │   ├── electron.js            # Electron main process
│   │   └── preload.js             # Electron security bridge
│   │
│   ├── package.json               # Dependencies & build config
│   ├── tsconfig.json              # TypeScript config
│   ├── tailwind.config.ts         # Tailwind config
│   └── node_modules/              # Dependencies
│
└── frontend_old/                   # Backup of old PyQt5 app
```

## 🔌 API Endpoints

All endpoints are relative to `http://localhost:8000/api/v1/ai`

### Load OCR Model
```http
POST /ocr_ai/load_model
Query Parameters:
  - model_path: string (file path to model)

Response:
{
  "success": true,
  "message": "Model loaded from ..."
}
```

### Configure OCR
```http
POST /ocr_ai/input_config
Query Parameters:
  - acceptance_threshold_ocr: float (0-1, default 0.5)
  - duplication_threshold_ocr: float (0-1, default 0.5)
  - row_threshold: int (default 20)

Response:
{
  "success": true,
  "message": "OCR configuration updated"
}
```

### Real-time OCR (WebSocket)
```
WS /ocr_ai/ws

Client → Server: Binary image data (JPEG/PNG)
Server → Client: JSON result
{
  "success": true,
  "text": "...",
  "confidence": 0.95,
  ...
}
```

## 🏗️ Architecture

### Frontend Stack
- **Framework:** Next.js 16 (React 19)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State:** Zustand
- **HTTP:** Axios
- **WebSocket:** ws
- **Desktop:** Electron + electron-builder

### Backend Stack
- **Framework:** FastAPI
- **Server:** Uvicorn
- **AI/ML:** PyTorch, YOLOv8, OpenCV
- **Language:** Python
- **Single Instance:** Windows Mutex

## 🔄 Data Flow

```
1. User opens app (Electron or browser)
   ↓
2. OCRPanel component renders
   ↓
3. Component connects to:
   - HTTP API (load model, configure)
   - WebSocket (real-time OCR)
   ↓
4. User uploads image
   ↓
5. Image sent via WebSocket to /ai/ocr_ai/ws
   ↓
6. Backend processes with Deep_Learning_Tool
   ↓
7. Results returned as JSON
   ↓
8. UI updates with results (preview + JSON)
```

## 📊 State Management (Zustand Store)

```typescript
useOCRStore {
  // State
  isConnected: boolean              // API connection
  isProcessing: boolean             // Processing status
  modelPath: string | null          // Loaded model path
  config: OCRConfig                 // Current thresholds
  wsConnected: boolean              // WebSocket status
  lastResult: any | null            // Last OCR result
  error: string | null              // Error message
  
  // Actions
  setConnected(bool)
  setConfig(config)                 // Updates via API
  setWSConnected(bool)
  setLastResult(result)
  setError(string)
  reset()
}
```

## 🔗 Component Hierarchy

```
next-app
├── app/layout.tsx
├── app/page.tsx
│   └── <OCRPanel />
│       ├── useOCRStore()          [Zustand hook]
│       ├── useOCRWebSocket()       [Custom hook]
│       ├── ocrApiClient            [API client instance]
│       └── JSX (buttons, sliders, canvas, etc.)
```

## 🧪 Testing

### Unit Tests (To be added)
```bash
npm run test
```

### Integration Tests
1. **API Connection:**
   - Start backend: `python main.py`
   - Start frontend: `npm run dev`
   - Check green status indicator

2. **WebSocket Connection:**
   - Upload test image
   - Check console for connection logs
   - Verify result displays

3. **Configuration:**
   - Adjust threshold sliders
   - Verify API receives updates
   - Check new config applied

## 📦 Building for Production

### Web (Static Export)
```bash
cd frontend
npm run build
npm run start
# Serves on http://localhost:3000
```

### Desktop (Electron Installer)
```bash
cd frontend
npm run electron-build
# Output:
# - frontend/dist/VisionCenter-OCR-Setup-1.0.0.exe (NSIS installer)
# - frontend/dist/VisionCenter-OCR-1.0.0.exe (Portable)
```

## 🐛 Troubleshooting

### WebSocket Connection Failed
- Check backend is running: `http://localhost:8000/api/docs`
- Check API URL in `.env.local` or code
- Check browser console for connection errors

### API Connection Failed
- Verify backend started: `python main.py`
- Verify port 8000 is not in use: `netstat -an | grep 8000`
- Check CORS settings in `api/app.py`

### TypeScript Errors
- Run: `npm run build` to check all types
- Check `tsconfig.json` for type rules

### Electron Won't Start
- Clear cache: `npm install electron --save-dev`
- Check Node version: `node --version` (should be 18+)
- Run: `npm run electron` directly

## 📝 Environment Variables

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 🔐 Security Notes

- ✅ Electron: Context isolation enabled
- ✅ Electron: No node integration in renderer
- ✅ API: CORS configured (adjust if needed)
- ⚠️ Backend: Single instance mutex (Windows only)

## 📚 Key Files Modified

| File | Changes |
|------|---------|
| `main.py` | Removed PyQt5 imports (lines 37-41) |
| `frontend/app/page.tsx` | Replaced boilerplate with OCRPanel |
| `frontend/package.json` | Added Electron scripts & config |
| `api/app.py` | No changes (still works) |

## 🎯 Next Phase (To Do)

- [ ] Add Database API endpoints
- [ ] Add PLC control API endpoints
- [ ] Add Camera acquisition API endpoints
- [ ] Migrate Login screen to Next.js
- [ ] Add authentication/session management
- [ ] Create settings management page
- [ ] Add image history storage
- [ ] Create export functionality
- [ ] Add unit & integration tests
- [ ] Optimize WebSocket performance
- [ ] Add progress indicators
- [ ] Create desktop shortcuts
- [ ] Sign executable (for distribution)

## 💡 Tips

1. **Dev with Electron:** Use `npm run electron-dev` for hot reload with desktop features
2. **API Debugging:** Visit `http://localhost:8000/api/docs` for Swagger UI
3. **Console Logs:** In Electron dev mode, DevTools opens automatically
4. **Responsive UI:** Tailwind classes handle mobile layouts
5. **Rebuilding:** After changing dependencies, run `npm install` then `npm run build`

## 📞 Support

For issues or questions:
1. Check console logs (F12 in browser, DevTools in Electron)
2. Review `api/backend/logs/api.log` for backend errors
3. Check WebSocket connection in Network tab
4. Review component props and state with React DevTools

---

**Last Updated:** 2026-06-08  
**Framework Versions:** Next.js 16, React 19, Electron 42, TypeScript 5, Tailwind 4
