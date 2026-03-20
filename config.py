import os

from dotenv import load_dotenv

load_dotenv()

TYPE = os.getenv("PRINTER_TYPE", "usb")
"""Printer type. Supported: usb, network."""

PROFILE = os.getenv("PRINTER_PROFILE", "TM-T88III")
"""Printer profile."""

match TYPE:
    case "usb":
        _vendor_id_str = os.getenv("PRINTER_VENDOR_ID", "0x04b8")
        VENDOR_ID = int(_vendor_id_str, 16)
        """Vendor ID in hex."""

        _product_id_str = os.getenv("PRINTER_PRODUCT_ID", "0x0202")
        PRODUCT_ID = int(_product_id_str, 16)
        """Product ID in hex."""
    case "network":
        ADDRESS = os.getenv("PRINTER_ADDRESS", "192.168.1.100")
    case _:
        raise ValueError(f"Printer type {TYPE} is not supported")
