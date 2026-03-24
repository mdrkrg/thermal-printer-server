from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import PrintError, PrintErrorResponse, PrintRequest, PrintResponse
from printer_service import PrinterService

global printer
printer: PrinterService


@asynccontextmanager
async def lifespan(app: FastAPI):
    global printer
    printer = PrinterService()
    yield
    printer.close()


app = FastAPI(
    title="Thermal Printer HTTP Server",
    description="HTTP API for controlling thermal printers via JSON with base64-encoded images",
    version="0.1.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    """Serve the printer frontend."""
    return templates.TemplateResponse("index.html", {"request": request})


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/print", response_model=PrintResponse)
async def print_job(request: PrintRequest) -> JSONResponse:
    """
    Print a sequence of items: text, QR codes, barcodes, and images.

    Images must be base64-encoded data URIs, e.g. `"source": "data:image/png;base64,..."`.
    Images wider than 512px are automatically resized.

    Example:
    ```json
    {
      "items": [
        {"type": "text", "content": "Hello, World!\\n"},
        {"type": "qr", "content": "https://example.com/"},
        {"type": "image", "source": "data:image/png;base64,..."},
        {"type": "barcode", "content": "123456789012", "format": "EAN13"}
      ]
    }
    ```
    """
    try:
        count, ms = printer.process_print_job(request.items)
        return JSONResponse(
            content=PrintResponse(
                success=True,
                items_processed=count,
                time_taken_ms=ms,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ).model_dump(by_alias=True)
        )
    except PrintError as e:
        return JSONResponse(
            content=PrintErrorResponse(
                error="Print Error",
                detail=str(e),
                items_processed=e.items_processed,
                time_taken_ms=e.time_taken_ms,
            ).model_dump(by_alias=True),
            status_code=e.status_code,
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "thermal-printer"}


@app.get("/status")
async def printer_status():
    """Query printer online status and paper level."""
    try:
        return JSONResponse(content=printer.get_status())
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Status Query Error",
                "detail": str(e),
                "online": False,
                "paperStatus": "unknown",
                "paperStatusCode": -1,
            },
            status_code=503,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
