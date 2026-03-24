from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic.alias_generators import to_camel

# Supported barcode formats from python-escpos
SUPPORTED_BARCODE_FORMATS = {
    "UPC-A",
    "UPC-E",
    "EAN13",
    "EAN8",
    "CODE39",
    "ITF",
    "NW7",
    "CODABAR",
    "CODE93",
    "CODE128",
    "GS1-128",
    "GS1 DATABAR OMNIDIRECTIONAL",
    "GS1 DATABAR TRUNCATED",
    "GS1 DATABAR LIMITED",
    "GS1 DATABAR EXPANDED",
}


class CamelCaseBaseModel(BaseModel):
    class Config:
        alias_generator = to_camel
        validate_by_name = True


class TextItem(CamelCaseBaseModel):
    """Print plain text."""

    type: Literal["text"] = "text"
    content: str


class QRItem(CamelCaseBaseModel):
    """Print QR code."""

    type: Literal["qr"] = "qr"
    content: str
    size: int = Field(default=3, ge=1, le=16, description="QR code pixel size (1-16)")
    center: bool = Field(default=False, description="Center the QR code")


class BarcodeItem(CamelCaseBaseModel):
    """Print barcode."""

    type: Literal["barcode"] = "barcode"
    content: str
    format: str = Field(description="Barcode format (e.g., EAN13, CODE128, CODE39)")
    height: int = Field(default=64, ge=1, le=255, description="Barcode height in dots")
    width: int = Field(default=3, ge=2, le=6, description="Barcode width in dots")
    text_position: Literal["ABOVE", "BELOW", "BOTH", "OFF"] = Field(
        default="BELOW", description="Position of human-readable text"
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v not in SUPPORTED_BARCODE_FORMATS:
            raise ValueError(
                f"Unsupported barcode format: {v}. "
                f"Supported formats: {', '.join(SUPPORTED_BARCODE_FORMATS)}"
            )
        return v


class ImageItem(CamelCaseBaseModel):
    """Print image from a base64-encoded data URI."""

    type: Literal["image"] = "image"
    source: str = Field(description="Base64 data URI, e.g. 'data:image/png;base64,...'")
    high_density_vertical: bool = True
    high_density_horizontal: bool = True
    impl: Literal["bitImageRaster", "graphics", "bitImageColumn"] = "bitImageRaster"
    fragment_height: int = Field(default=960, ge=1)
    center: bool = False


class CutItem(CamelCaseBaseModel):
    """Control paper cutting."""

    type: Literal["cut"] = "cut"
    enabled: bool = Field(
        default=True,
        description=(
            "If true, cut paper at this position. "
            "If false at end of payload, disable auto-cut. "
            "If false in middle, ignored."
        ),
    )


# Discriminated union of all print items
PrintItem = Annotated[
    TextItem | QRItem | BarcodeItem | ImageItem | CutItem,
    Field(discriminator="type"),
]


class PrintRequest(CamelCaseBaseModel):
    """Request to print a sequence of items."""

    items: list[PrintItem] = Field(description="Array of items to print in sequence")


class PrintResponse(CamelCaseBaseModel):
    """Response from print operation."""

    success: bool
    items_processed: int
    time_taken_ms: int
    timestamp: str


@dataclass
class PrintError(Exception):
    """Error thrown from PrinterService."""

    message: object
    items_processed: int
    time_taken_ms: int
    status_code: int = 500

    def __post_init__(self):
        super().__init__(self.message)


class PrintErrorResponse(CamelCaseBaseModel):
    """Error response from print operation."""

    success: Literal[False] = False
    error: str
    detail: str | None = None
    item_index: int | None = None
    items_processed: int
    time_taken_ms: int
