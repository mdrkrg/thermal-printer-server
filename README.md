# Thermal Printer HTTP Server

FastAPI-based HTTP server for controlling thermal printers. Supports printing text, QR codes, barcodes, and images with automatic resizing.

## Features

- **Text Printing**: Free-form text output
- **QR Codes**: Generate QR codes from strings
- **Barcodes**: Support for 15+ barcode formats (EAN13, CODE128, CODE39, etc.)
- **Images**: Base64-encoded images with automatic resizing to max 512px width
- **Paper Cutting**: Configurable paper cut control
- **Printer Status**: Query online status and paper level
- **Web UI**: Built-in browser interface for building and sending print jobs

## Installation

Clone the repository and install dependencies:

```bash
uv sync
```

Configure your printer by copying `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your printer's USB IDs:

```bash
# Find your printer's USB IDs
lsusb

# Example output:
# Bus 001 Device 001: ID 0202:04b8 TM-T88III

# Update .env with the vendor and product IDs
PRINTER_VENDOR_ID=0x0202
PRINTER_PRODUCT_ID=0x04b8
PRINTER_PROFILE=TM-T88III
```

## Configuration

See `.env.example` for more detailed explanations of environment variables.

## Usage

### Start the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

### Web UI

Open `http://localhost:8000` in a browser to access the built-in interface. It lets you:

- Check printer status (online/offline, paper level)
- Build a print job by adding items one at a time (text, QR, barcode, image, cut)
- Reorder and remove items before sending
- Upload images directly from disk (converted to base64 automatically)
- Preview the JSON payload before printing
- Send the job and see the response

### API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Examples

### 0. Check Printer Status

```bash
curl http://localhost:8000/status
```

Response:

```json
{
  "online": true,
  "paper_status": "adequate",
  "paper_status_code": 2
}
```

Paper status values:

- `"adequate"` (code 2): Paper is adequate
- `"low"` (code 1): Paper is running low
- `"out"` (code 0): No paper
- `"unknown"` (code -1): Unable to query status

### 1. Simple Text Receipt

```bash
curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "text", "content": "RECEIPT\n"},
      {"type": "text", "content": "Item: Coffee - $3.50\n"},
      {"type": "text", "content": "Total: $3.50\n"}
    ]
  }'
```

### 2. QR Code

```bash
curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "text", "content": "Scan for details:\n"},
      {"type": "qr", "content": "https://example.com/receipt/123", "center": true, "size": 4}
    ]
  }'
```

### 3. Barcode

```bash
curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "text", "content": "Product Barcode:\n"},
      {"type": "barcode", "content": "123456789012", "format": "EAN13", "height": 64, "width": 3}
    ]
  }'
```

### 4. Image with Base64

```bash
curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "image", "source": "data:image/png;base64,iVBORw0KGgoAAAANS...", "center": true},
      {"type": "text", "content": "Thank you!\n"}
    ]
  }'
```

### 5. Complete Receipt Example

```bash
curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "text", "content": "================================\n"},
      {"type": "text", "content": "        COFFEE SHOP\n"},
      {"type": "text", "content": "================================\n"},
      {"type": "text", "content": "\n"},
      {"type": "text", "content": "Date: 2026-03-17 10:30 AM\n"},
      {"type": "text", "content": "Order #: 12345\n"},
      {"type": "text", "content": "\n"},
      {"type": "text", "content": "1x Espresso          $3.50\n"},
      {"type": "text", "content": "1x Croissant         $4.00\n"},
      {"type": "text", "content": "--------------------------------\n"},
      {"type": "text", "content": "Total:               $7.50\n"},
      {"type": "text", "content": "\n"},
      {"type": "qr", "content": "https://example.com/receipt/12345", "center": true},
      {"type": "text", "content": "\n"},
      {"type": "text", "content": "Thank you for your visit!\n"}
    ]
  }'
```

### 6. Control Paper Cutting

```bash
# Explicit cut in the middle
curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "text", "content": "First receipt\n"},
      {"type": "cut", "enabled": true},
      {"type": "text", "content": "Second receipt\n"}
    ]
  }'

# Disable auto-cut at end
curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"type": "text", "content": "Part 1 of continuous print\n"},
      {"type": "cut", "enabled": false}
    ]
  }'
```

## Request Format

### JSON Request Body

```json
{
  "items": [
    {
      "type": "text",
      "content": "Hello, World!\n"
    },
    {
      "type": "qr",
      "content": "https://example.com",
      "size": 3,
      "center": false
    },
    {
      "type": "barcode",
      "content": "123456789012",
      "format": "EAN13",
      "height": 64,
      "width": 3,
      "text_position": "BELOW"
    },
    {
      "type": "image",
      "source": "data:image/png;base64,...",
      "center": false
    },
    {
      "type": "cut",
      "enabled": true
    }
  ]
}
```

### Item Types

#### Text Item

```json
{
  "type": "text",
  "content": "Your text here\n"
}
```

#### QR Code Item

```json
{
  "type": "qr",
  "content": "https://example.com",
  "size": 3,        // Optional: 1-16, default 3
  "center": false   // Optional: default false
}
```

#### Barcode Item

```json
{
  "type": "barcode",
  "content": "123456789012",
  "format": "EAN13",         // Required: see supported formats below
  "height": 64,              // Optional: 1-255, default 64
  "width": 3,                // Optional: 2-6, default 3
  "text_position": "BELOW"   // Optional: ABOVE, BELOW, BOTH, OFF
}
```

**Supported Barcode Formats:**

- UPC-A, UPC-E
- EAN13, EAN8
- CODE39, CODE93, CODE128
- ITF, NW7, CODABAR
- GS1-128
- GS1 DATABAR OMNIDIRECTIONAL, TRUNCATED, LIMITED, EXPANDED

#### Image Item

```json
{
  "type": "image",
  "source": "data:image/png;base64,...",  // Required: base64 data URI
  "high_density_vertical": true,          // Optional: default true
  "high_density_horizontal": true,        // Optional: default true
  "impl": "bitImageRaster",               // Optional: bitImageRaster, graphics, or bitImageColumn
  "fragment_height": 960,                 // Optional: default 960
  "center": false                         // Optional: default false
}
```

Images must be base64-encoded data URIs (e.g., `data:image/png;base64,iVBORw0KG...`).
Images wider than 512px are automatically resized while maintaining aspect ratio.

**Image Implementations:**

- `bitImageRaster`: prints with GS v 0 command (default)
- `graphics`: prints with GS ( L command
- `bitImageColumn`: prints with ESC * command

#### Cut Item

```json
{
  "type": "cut",
  "enabled": true
}
```

**Cut Behavior:**

- `cut: true` anywhere → cuts paper at that position
- `cut: false` at end → disables auto-cut
- `cut: false` in middle → ignored
- Default: auto-cut at end if no explicit `cut: false`

## Response Format

### Success Response

```json
{
  "success": true,
  "items_processed": 5,
  "time_taken_ms": 1234,
  "timestamp": "2026-03-17T10:30:45.123456Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Validation Error",
  "detail": "Unsupported barcode format: INVALID",
  "item_index": 3,
  "items_processed": 2,
  "time_taken_ms": 456
}
```

## Error Handling

- **400 Bad Request**: Invalid payload, unsupported barcode format, invalid image base64
- **500 Internal Server Error**: Printer offline, paper out, hardware error

On any error during printing, the paper is automatically cut to separate the partial print.
