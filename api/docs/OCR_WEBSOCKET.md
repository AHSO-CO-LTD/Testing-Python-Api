# OCR WebSocket API

This document explains how to use the OCR WebSocket endpoint from any client
language or platform that supports WebSocket binary messages.

## Overview

The OCR WebSocket endpoint is used for real-time OCR prediction.

The client sends one encoded image as a binary WebSocket message. The server
decodes the image, runs OCR, and sends one JSON response.

```text
Client                         Server
  |                               |
  | --- binary image bytes -----> |
  |                               | Decode image and run OCR
  | <-------- JSON result ------- |
  |                               |
```

## Endpoint

Local development:

```text
ws://localhost:8000/api/v1/ai/ocr_ai/ws
```

Production format:

```text
ws://<host>:<port>/api/v1/ai/ocr_ai/ws
wss://<domain>/api/v1/ai/ocr_ai/ws
```

Use `ws://` for plain WebSocket and `wss://` when the API is served behind
HTTPS/TLS.

## Documentation Helper

Swagger and ReDoc are based on OpenAPI, and OpenAPI does not show WebSocket
routes as normal interactive API operations.

For documentation visibility, the API also exposes:

```http
GET /api/v1/ai/ocr_ai/ws
```

This `GET` endpoint only returns WebSocket metadata. It does not run OCR
prediction.

Use this endpoint for prediction:

```text
WS /api/v1/ai/ocr_ai/ws
```

## Required HTTP Setup

Before sending images to the WebSocket, the OCR model must be loaded and the OCR
configuration should be set.

### Load OCR Model

```http
POST /api/v1/ai/ocr_ai/load_model?model_path=<model_path>
```

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/ocr_ai/load_model?model_path=E:/models/ocr_model.pth"
```

Success response:

```json
{
  "success": true,
  "message": "Model loaded from E:/models/ocr_model.pth"
}
```

Error response:

```json
{
  "success": false,
  "error": "Model file not found: E:/models/ocr_model.pth"
}
```

### Set OCR Configuration

```http
POST /api/v1/ai/ocr_ai/input_config?acceptance_threshold_ocr=0.5&duplication_threshold_ocr=0.5&row_threshold=20
```

Parameters:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `acceptance_threshold_ocr` | `float` | `0.5` | OCR acceptance threshold. Must be from `0` to `1`. |
| `duplication_threshold_ocr` | `float` | `0.5` | OCR duplication threshold. Must be from `0` to `1`. |
| `row_threshold` | `int` | `20` | OCR row grouping threshold. Must be `0` or greater. |

Success response:

```json
{
  "success": true,
  "message": "OCR configuration updated"
}
```

## WebSocket Protocol

### Connection

The client opens a WebSocket connection to:

```text
ws://localhost:8000/api/v1/ai/ocr_ai/ws
```

The server accepts the connection immediately.

### Request Message

Send one image per WebSocket binary frame.

Message type:

```text
Binary frame
```

Message body:

```text
Raw encoded image bytes
```

Recommended image formats:

```text
JPEG
PNG
BMP
```

The server decodes the binary payload with OpenCV. Any encoded image format
supported by the deployed OpenCV build can be used.

Do not send:

```text
JSON object
Base64 string
multipart/form-data
HTTP file upload body
Text WebSocket frame
```

### Response Message

For each valid binary image message, the server returns one JSON text message.

Success:

```json
{
  "success": true,
  "text": "recognized text"
}
```

Failure:

```json
{
  "success": false,
  "error": "error message"
}
```

## Client Flow

```text
1. Call HTTP load_model.
2. Call HTTP input_config.
3. Connect to WebSocket.
4. Read an image file as bytes.
5. Send the image bytes as a binary WebSocket message.
6. Receive one JSON response.
7. Repeat steps 4-6 for more images.
8. Close the WebSocket connection.
```

For ordered processing, send one image and wait for its response before sending
the next image.

## Language-Neutral Pseudocode

```text
http_post("/api/v1/ai/ocr_ai/load_model", query={
  "model_path": "E:/models/ocr_model.pth"
})

http_post("/api/v1/ai/ocr_ai/input_config", query={
  "acceptance_threshold_ocr": 0.5,
  "duplication_threshold_ocr": 0.5,
  "row_threshold": 20
})

ws = websocket_connect("ws://localhost:8000/api/v1/ai/ocr_ai/ws")

image_bytes = read_file_as_bytes("sample.jpg")
ws.send_binary(image_bytes)

json_text = ws.receive_text()
result = json_parse(json_text)

ws.close()
```

## Browser JavaScript Example

```html
<input id="imageInput" type="file" accept="image/*" />
<button id="sendButton">Send OCR</button>
<pre id="output"></pre>

<script>
const ws = new WebSocket("ws://localhost:8000/api/v1/ai/ocr_ai/ws");
ws.binaryType = "arraybuffer";

ws.onopen = () => {
  console.log("WebSocket connected");
};

ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  document.getElementById("output").textContent = JSON.stringify(result, null, 2);
};

ws.onerror = (event) => {
  console.error("WebSocket error", event);
};

ws.onclose = () => {
  console.log("WebSocket closed");
};

document.getElementById("sendButton").onclick = async () => {
  const file = document.getElementById("imageInput").files[0];
  if (!file) {
    return;
  }

  const imageBytes = await file.arrayBuffer();
  ws.send(imageBytes);
};
</script>
```

## Node.js Example

Install dependency:

```bash
npm install ws
```

Client:

```javascript
const fs = require("fs");
const WebSocket = require("ws");

const ws = new WebSocket("ws://localhost:8000/api/v1/ai/ocr_ai/ws");

ws.on("open", () => {
  const imageBytes = fs.readFileSync("sample.jpg");
  ws.send(imageBytes);
});

ws.on("message", (data) => {
  const result = JSON.parse(data.toString());
  console.log(result);
  ws.close();
});

ws.on("error", (error) => {
  console.error(error);
});
```

## Python Example

Install dependencies:

```bash
pip install requests websocket-client
```

Client:

```python
import json
import requests
import websocket

HTTP_BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/ai/ocr_ai/ws"

requests.post(
    f"{HTTP_BASE_URL}/ai/ocr_ai/load_model",
    params={"model_path": r"E:/models/ocr_model.pth"},
    timeout=30,
).raise_for_status()

requests.post(
    f"{HTTP_BASE_URL}/ai/ocr_ai/input_config",
    params={
        "acceptance_threshold_ocr": 0.5,
        "duplication_threshold_ocr": 0.5,
        "row_threshold": 20,
    },
    timeout=30,
).raise_for_status()

ws = websocket.WebSocket()
ws.connect(WS_URL)

try:
    with open("sample.jpg", "rb") as image_file:
        ws.send_binary(image_file.read())

    result = json.loads(ws.recv())
    print(result)
finally:
    ws.close()
```

## C# .NET Example

```csharp
using System.Net.WebSockets;
using System.Text;

using var ws = new ClientWebSocket();

await ws.ConnectAsync(
    new Uri("ws://localhost:8000/api/v1/ai/ocr_ai/ws"),
    CancellationToken.None
);

byte[] imageBytes = await File.ReadAllBytesAsync("sample.jpg");

await ws.SendAsync(
    imageBytes,
    WebSocketMessageType.Binary,
    endOfMessage: true,
    cancellationToken: CancellationToken.None
);

byte[] buffer = new byte[1024 * 1024];
WebSocketReceiveResult response = await ws.ReceiveAsync(
    buffer,
    CancellationToken.None
);

string json = Encoding.UTF8.GetString(buffer, 0, response.Count);
Console.WriteLine(json);

await ws.CloseAsync(
    WebSocketCloseStatus.NormalClosure,
    "done",
    CancellationToken.None
);
```

## Java Example

This example uses the standard Java 11+ WebSocket client.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.CountDownLatch;

public class OcrWebSocketClient {
    public static void main(String[] args) throws Exception {
        CountDownLatch done = new CountDownLatch(1);

        WebSocket ws = HttpClient.newHttpClient()
            .newWebSocketBuilder()
            .buildAsync(
                URI.create("ws://localhost:8000/api/v1/ai/ocr_ai/ws"),
                new WebSocket.Listener() {
                    @Override
                    public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
                        System.out.println(data);
                        done.countDown();
                        return WebSocket.Listener.super.onText(webSocket, data, last);
                    }

                    @Override
                    public void onError(WebSocket webSocket, Throwable error) {
                        error.printStackTrace();
                        done.countDown();
                    }
                }
            )
            .join();

        byte[] imageBytes = Files.readAllBytes(Path.of("sample.jpg"));
        ws.sendBinary(ByteBuffer.wrap(imageBytes), true).join();

        done.await();
        ws.sendClose(WebSocket.NORMAL_CLOSURE, "done").join();
    }
}
```

## Go Example

This example uses `github.com/gorilla/websocket`.

Install dependency:

```bash
go get github.com/gorilla/websocket
```

Client:

```go
package main

import (
	"fmt"
	"log"
	"os"

	"github.com/gorilla/websocket"
)

func main() {
	url := "ws://localhost:8000/api/v1/ai/ocr_ai/ws"

	conn, _, err := websocket.DefaultDialer.Dial(url, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	imageBytes, err := os.ReadFile("sample.jpg")
	if err != nil {
		log.Fatal(err)
	}

	if err := conn.WriteMessage(websocket.BinaryMessage, imageBytes); err != nil {
		log.Fatal(err)
	}

	_, response, err := conn.ReadMessage()
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(string(response))
}
```

## Error Handling

Common error responses:

| Error | Meaning | Fix |
| --- | --- | --- |
| `Model not loaded. Call load_model() first` | OCR model is not loaded. | Call `POST /api/v1/ai/ocr_ai/load_model` before prediction. |
| `img_ocr cannot be None or empty` | The binary payload could not be decoded into an image. | Send raw JPEG/PNG/BMP image bytes. |
| `acceptance_threshold_ocr must be between 0 and 1` | Invalid acceptance threshold. | Set a value from `0` to `1`. |
| `duplication_threshold_ocr must be between 0 and 1` | Invalid duplication threshold. | Set a value from `0` to `1`. |
| `row_threshold must be non-negative` | Invalid row threshold. | Set a value of `0` or greater. |

## Operational Notes

- Keep one WebSocket connection open if sending many images.
- Send one image per binary message.
- The server sends one JSON response per image.
- Close the connection when prediction is complete.
- For browser clients hosted on HTTPS, use `wss://` instead of `ws://`.
- If using a reverse proxy, make sure it supports WebSocket upgrade headers.

## Reverse Proxy Requirements

When the API is deployed behind a proxy such as Nginx, the proxy must allow
WebSocket upgrades.

Typical required headers:

```text
Upgrade: websocket
Connection: Upgrade
```

## Quick Checklist

Before reporting a client integration issue, verify:

- The API server is running.
- The model was loaded successfully.
- OCR config was submitted successfully.
- The WebSocket URL starts with `ws://` or `wss://`.
- The client sends a binary WebSocket frame.
- The binary payload is an encoded image file, not Base64 text.
- The client waits for a JSON text response.
