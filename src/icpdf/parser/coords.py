"""Frozen page-coordinate model.

All parser output uses PyMuPDF's `page.rect` display space: origin top-left,
unit = PDF point, after CropBox and /Rotate. This module is the only place that
converts between points and rendered-pixel coordinates.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from icpdf.domain.common import BBox


class PageGeometry(BaseModel):
    """Per-page geometry + render mapping. Stored in every run artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    page_number: int
    mediabox: BBox
    cropbox: BBox
    rect: BBox
    rotation: int
    dpi: float
    zoom: float
    pixel_width: int
    pixel_height: int

    @model_validator(mode="after")
    def _check(self) -> "PageGeometry":
        if self.page_number < 1:
            raise ValueError("page_number must be >= 1")
        if self.rotation % 90 != 0:
            raise ValueError("rotation must be a multiple of 90")
        if self.dpi <= 0 or self.zoom <= 0:
            raise ValueError("dpi/zoom must be positive")
        if self.pixel_width <= 0 or self.pixel_height <= 0:
            raise ValueError("pixel size must be positive")
        return self

    @classmethod
    def from_page(cls, page, dpi: float, page_number: int) -> "PageGeometry":
        rect = page.rect
        zoom = float(dpi) / 72.0
        return cls(
            page_number=page_number,
            mediabox=tuple(page.mediabox),  # type: ignore[arg-type]
            cropbox=tuple(page.cropbox),    # type: ignore[arg-type]
            rect=(rect.x0, rect.y0, rect.x1, rect.y1),
            rotation=int(page.rotation),
            dpi=float(dpi),
            zoom=zoom,
            pixel_width=round(rect.width * zoom),
            pixel_height=round(rect.height * zoom),
        )

    def point_to_pixel(self, x: float, y: float) -> tuple[float, float]:
        return ((x - self.rect[0]) * self.zoom, (y - self.rect[1]) * self.zoom)

    def pixel_to_point(self, px: float, py: float) -> tuple[float, float]:
        return (px / self.zoom + self.rect[0], py / self.zoom + self.rect[1])

    def bbox_to_pixel(self, bbox: BBox) -> tuple[float, float, float, float]:
        x0, y0 = self.point_to_pixel(bbox[0], bbox[1])
        x1, y1 = self.point_to_pixel(bbox[2], bbox[3])
        return (x0, y0, x1, y1)

    def pixel_to_bbox(self, pixel_bbox: tuple[float, float, float, float]) -> BBox:
        x0, y0 = self.pixel_to_point(pixel_bbox[0], pixel_bbox[1])
        x1, y1 = self.pixel_to_point(pixel_bbox[2], pixel_bbox[3])
        return (x0, y0, x1, y1)

    def clamp_bbox(self, bbox: BBox) -> BBox:
        """Clamp a bbox into page.rect (PDF text can slightly exceed the crop)."""
        x0, y0, x1, y1 = bbox
        return (
            max(self.rect[0], min(x0, self.rect[2])),
            max(self.rect[1], min(y0, self.rect[3])),
            max(self.rect[0], min(x1, self.rect[2])),
            max(self.rect[1], min(y1, self.rect[3])),
        )

    def to_display_bbox(self, bbox: BBox) -> BBox:
        """Convert PyMuPDF text bbox (unrotated user space) into page.rect space.

        Empirically (PyMuPDF 2.0), `Page.get_text()` returns bboxes in the
        **unrotated** PDF user space for every `/Rotate` value, and does not
        subtract a non-zero CropBox origin. `page.rect` is post-crop/post-rotate.

        Algorithm: subtract the CropBox origin, rotate by /Rotate into the
        display rectangle, then rebase onto `page.rect` origin.
        """
        cx0, cy0, cx1, cy1 = self.cropbox
        width, height = cx1 - cx0, cy1 - cy0
        u0, v0 = bbox[0] - cx0, bbox[1] - cy0
        u1, v1 = bbox[2] - cx0, bbox[3] - cy0
        r = self.rotation % 360
        if r == 0:
            xs, ys = (u0, u1), (v0, v1)
        elif r == 90:
            xs, ys = (height - v1, height - v0), (u0, u1)
        elif r == 180:
            xs, ys = (width - u1, width - u0), (height - v1, height - v0)
        else:                                                   # 270
            xs, ys = (v0, v1), (width - u1, width - u0)
        return self.clamp_bbox((
            self.rect[0] + min(xs), self.rect[1] + min(ys),
            self.rect[0] + max(xs), self.rect[1] + max(ys),
        ))
