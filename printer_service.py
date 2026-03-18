import base64
import time
from io import BytesIO
from typing import Any

from escpos.printer import Usb
from PIL import Image

import config
from models import (
    BarcodeItem,
    CutItem,
    ImageItem,
    PrintError,
    PrintItem,
    QRItem,
    TextItem,
)


class PrinterService:
    """Service for handling thermal printer operations."""

    def __init__(self):
        """Initialize printer connection."""
        self.printer = Usb(
            idVendor=config.VENDOR_ID,
            idProduct=config.PRODUCT_ID,
            in_ep=config.IN_EP,
            profile=config.PROFILE,
        )

    def process_print_job(self, items: list[PrintItem]) -> tuple[int, int]:
        """
        Process a print job with multiple items.

        Returns:
            Tuple of (items_processed, time_taken_ms)
        """
        start_time = time.time()
        items_processed = 0
        explicit_cut_at_end = None

        try:
            for i, item in enumerate(items):
                is_last = i == len(items) - 1

                if isinstance(item, CutItem):
                    if is_last:
                        explicit_cut_at_end = item.enabled
                    elif item.enabled:
                        self.printer.cut()
                    # cut=false in the middle is ignored
                else:
                    self._process_item(item)
                    items_processed += 1

            # Auto-cut unless explicitly disabled at end
            if explicit_cut_at_end is None or explicit_cut_at_end:
                self.printer.cut()

        except (ValueError, Exception) as e:
            try:
                self.printer.cut()
            except Exception:
                pass
            time_taken_ms = int((time.time() - start_time) * 1000)
            raise PrintError(
                str(e),
                items_processed=items_processed,
                time_taken_ms=time_taken_ms,
                status_code=400 if isinstance(e, ValueError) else 500,
            ) from e

        time_taken_ms = int((time.time() - start_time) * 1000)
        return items_processed, time_taken_ms

    def _process_item(self, item: PrintItem) -> None:
        match item:
            case TextItem(content=text):
                self.printer.text(text)
            case QRItem(content=code, size=s, center=c):
                self.printer.qr(code, size=s, center=c)
            case BarcodeItem(
                content=bc, format=fmt, height=h, width=w, text_position=pos
            ):
                self.printer.barcode(bc, fmt, height=h, width=w, pos=pos)
            case ImageItem():
                self._process_image(item)

    def _process_image(self, item: ImageItem) -> None:
        """Load image from base64 data URI, resize if needed, and print."""
        try:
            header, data = item.source.split(",", 1)
            # Parse MIME type from header like "data:image/png;base64"
            mime = header.split(":")[1].split(";")[0]  # e.g. "image/png"
            subtype = mime.split("/")[1]  # e.g. "png"

            # Map MIME subtype to Pillow format
            ext_map = Image.registered_extensions()
            img_format = ext_map.get(f".{subtype}") or ext_map.get(
                f".{subtype.lower()}"
            )
            if not img_format:
                # Fallback to PNG
                img_format = "PNG"

            img = Image.open(BytesIO(base64.b64decode(data)))
        except Exception as e:
            raise ValueError(f"Invalid base64 image data: {e}")

        if img.width > 512:
            new_height = int(img.height * 512 / img.width)
            img = img.resize((512, new_height), Image.Resampling.LANCZOS)

        buf = BytesIO()
        img.save(buf, format=img_format)
        buf.seek(0)
        self.printer.image(
            buf,
            high_density_vertical=item.high_density_vertical,
            high_density_horizontal=item.high_density_horizontal,
            impl=item.impl,
            fragment_height=item.fragment_height,
            center=item.center,
        )

    def get_status(self) -> dict[str, Any]:
        """Query printer online and paper status."""
        try:
            is_online = self.printer.is_online()
        except Exception:
            is_online = False

        try:
            paper_code = self.printer.paper_status()
            paper_status = {2: "adequate", 1: "low", 0: "out"}.get(
                paper_code, "unknown"
            )
        except Exception:
            paper_code = -1
            paper_status = "unknown"

        return {
            "online": is_online,
            "paper_status": paper_status,
            "paper_status_code": paper_code,
        }

    def close(self) -> None:
        self.printer.close()
