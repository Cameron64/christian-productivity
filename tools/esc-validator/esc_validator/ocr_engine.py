"""
OCR Engine Abstraction Layer (Phase 4.1)

Provides unified interface for multiple OCR engines (PaddleOCR, Tesseract)
with automatic fallback and caching support.
"""

import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pytesseract

logger = logging.getLogger(__name__)

# Configure Tesseract path for Windows
if sys.platform == "win32":
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in tesseract_paths:
        if Path(path).exists():
            pytesseract.pytesseract.tesseract_cmd = path
            logger.debug(f"Tesseract found at: {path}")
            break


@dataclass
class OCRResult:
    """Unified OCR result format across all engines."""
    text: str
    confidence: float  # Normalized 0-100
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) - left, top, right, bottom

    @property
    def x(self) -> int:
        """Left coordinate."""
        return self.bbox[0]

    @property
    def y(self) -> int:
        """Top coordinate."""
        return self.bbox[1]

    @property
    def width(self) -> int:
        """Width of bounding box."""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        """Height of bounding box."""
        return self.bbox[3] - self.bbox[1]

    @property
    def center_x(self) -> float:
        """Center X coordinate."""
        return (self.bbox[0] + self.bbox[2]) / 2

    @property
    def center_y(self) -> float:
        """Center Y coordinate."""
        return (self.bbox[1] + self.bbox[3]) / 2

    def __str__(self) -> str:
        return f"'{self.text}' (conf: {self.confidence:.1f}%) at ({self.x}, {self.y})"


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    @abstractmethod
    def extract_text(
        self,
        image: np.ndarray,
        lang: str = "eng",
        min_confidence: float = 0.0
    ) -> List[OCRResult]:
        """
        Extract text with bounding boxes from image.

        Args:
            image: Preprocessed image as numpy array (grayscale or BGR)
            lang: Language code (default: "eng")
            min_confidence: Minimum confidence threshold (0-100)

        Returns:
            List of OCRResult objects
        """
        pass

    @abstractmethod
    def get_engine_name(self) -> str:
        """Return the name of the OCR engine."""
        pass


class PaddleOCREngine(OCREngine):
    """PaddleOCR-based engine (primary, fast, accurate)."""

    def __init__(self, lang: str = "en", use_gpu: bool = False):
        """
        Initialize PaddleOCR engine.

        Args:
            lang: Language code (default: "en")
            use_gpu: Whether to use GPU acceleration (ignored in PaddleOCR 3.x - uses CPU by default)
        """
        try:
            from paddleocr import PaddleOCR
            # Note: PaddleOCR 3.x has different API - simpler initialization
            # GPU support would require different installation (paddlepaddle-gpu)
            self.ocr = PaddleOCR(lang=lang)
            logger.info(f"PaddleOCR engine initialized (lang: {lang})")
        except ImportError as e:
            logger.error(f"PaddleOCR not available: {e}")
            raise RuntimeError("PaddleOCR not installed. Install with: pip install paddleocr")
        except Exception as e:
            logger.error(f"PaddleOCR initialization failed: {e}")
            raise RuntimeError(f"PaddleOCR initialization failed: {e}")

    def extract_text(
        self,
        image: np.ndarray,
        lang: str = "eng",
        min_confidence: float = 0.0
    ) -> List[OCRResult]:
        """
        Extract text with bounding boxes using PaddleOCR.

        Args:
            image: Preprocessed image as numpy array
            lang: Language code (ignored, set during init)
            min_confidence: Minimum confidence threshold (0-100)

        Returns:
            List of OCRResult objects
        """
        logger.debug("Running PaddleOCR text extraction")

        try:
            # PaddleOCR expects BGR image (OpenCV format)
            # If grayscale, convert to BGR
            if len(image.shape) == 2:
                import cv2
                image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                image_bgr = image

            # Run OCR (PaddleOCR 3.x API - no cls parameter)
            result = self.ocr.ocr(image_bgr)

            if result is None or len(result) == 0:
                logger.warning("PaddleOCR returned no results")
                return []

            # Parse results
            ocr_results = []
            for line in result:
                if line is None:
                    continue

                for detection in line:
                    # detection format: [[bbox_coords], text_info] where text_info can be dict or tuple
                    # PaddleOCR 3.x MCP: [[bbox], {'transcription': text, 'score': conf}]
                    # PaddleOCR 2.x: [[bbox], (text, conf)]
                    try:
                        bbox_coords = detection[0]
                        text_info = detection[1]

                        # Handle both dict and tuple formats
                        if isinstance(text_info, dict):
                            text = text_info.get('transcription', text_info.get('text', ''))
                            confidence = text_info.get('score', text_info.get('confidence', 0.0))
                        elif isinstance(text_info, (tuple, list)) and len(text_info) >= 2:
                            text, confidence = text_info[0], text_info[1]
                        else:
                            logger.warning(f"Unexpected text_info format: {text_info}")
                            continue
                    except (ValueError, IndexError, KeyError) as e:
                        logger.warning(f"Failed to parse detection: {e}, detection format: {detection}")
                        continue

                    # bbox_coords is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    # Extract min/max for axis-aligned bounding box
                    x_coords = [pt[0] for pt in bbox_coords]
                    y_coords = [pt[1] for pt in bbox_coords]
                    x1, x2 = int(min(x_coords)), int(max(x_coords))
                    y1, y2 = int(min(y_coords)), int(max(y_coords))

                    # Normalize confidence to 0-100 (PaddleOCR returns 0-1)
                    confidence_pct = confidence * 100

                    # Filter by confidence
                    if confidence_pct < min_confidence:
                        continue

                    # Clean text
                    text = text.strip()
                    if not text:
                        continue

                    ocr_results.append(OCRResult(
                        text=text,
                        confidence=confidence_pct,
                        bbox=(x1, y1, x2, y2)
                    ))

            logger.info(f"PaddleOCR extracted {len(ocr_results)} text elements")
            return ocr_results

        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return []

    def get_engine_name(self) -> str:
        return "PaddleOCR"


class TesseractOCREngine(OCREngine):
    """Tesseract-based engine (fallback, widely available)."""

    def __init__(self):
        """Initialize Tesseract engine."""
        logger.info("Tesseract engine initialized")

    def extract_text(
        self,
        image: np.ndarray,
        lang: str = "eng",
        min_confidence: float = 0.0
    ) -> List[OCRResult]:
        """
        Extract text with bounding boxes using Tesseract.

        Args:
            image: Preprocessed image as numpy array (grayscale)
            lang: Tesseract language (default: "eng")
            min_confidence: Minimum confidence threshold (0-100)

        Returns:
            List of OCRResult objects
        """
        logger.debug("Running Tesseract text extraction")

        try:
            # Configure Tesseract for technical drawings
            custom_config = r'--psm 6 --oem 3'

            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(
                image,
                lang=lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )

            ocr_results = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = float(data['conf'][i])

                # Skip empty text and low confidence
                if not text or confidence < 0:
                    continue

                if confidence < min_confidence:
                    continue

                # Extract bounding box (Tesseract format: x, y, w, h)
                x = int(data['left'][i])
                y = int(data['top'][i])
                w = int(data['width'][i])
                h = int(data['height'][i])

                # Convert to (x1, y1, x2, y2) format
                bbox = (x, y, x + w, y + h)

                ocr_results.append(OCRResult(
                    text=text,
                    confidence=confidence,
                    bbox=bbox
                ))

            logger.info(f"Tesseract extracted {len(ocr_results)} text elements")
            return ocr_results

        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return []

    def get_engine_name(self) -> str:
        return "Tesseract"


def get_ocr_engine(engine: str = "paddleocr", use_gpu: bool = False) -> OCREngine:
    """
    Factory function to create OCR engine.

    Args:
        engine: Engine name ("paddleocr" or "tesseract")
        use_gpu: Whether to use GPU (PaddleOCR only)

    Returns:
        OCREngine instance

    Raises:
        ValueError: If engine name is invalid
        RuntimeError: If requested engine is not available
    """
    engine_lower = engine.lower()

    if engine_lower == "paddleocr":
        try:
            return PaddleOCREngine(use_gpu=use_gpu)
        except RuntimeError as e:
            logger.warning(f"PaddleOCR not available, falling back to Tesseract: {e}")
            return TesseractOCREngine()

    elif engine_lower == "tesseract":
        return TesseractOCREngine()

    else:
        raise ValueError(f"Unknown OCR engine: {engine}. Choose 'paddleocr' or 'tesseract'")


# Global OCR cache for Phase 1 → Phase 4 sharing
_ocr_cache: Optional[List[OCRResult]] = None


def set_ocr_cache(results: List[OCRResult]) -> None:
    """
    Cache OCR results for reuse across phases.

    Args:
        results: List of OCRResult objects
    """
    global _ocr_cache
    _ocr_cache = results
    logger.debug(f"OCR cache populated with {len(results)} results")


def get_ocr_cache() -> Optional[List[OCRResult]]:
    """
    Retrieve cached OCR results.

    Returns:
        Cached OCRResult list or None if cache is empty
    """
    return _ocr_cache


def clear_ocr_cache() -> None:
    """Clear the OCR cache to free memory."""
    global _ocr_cache
    if _ocr_cache is not None:
        logger.debug(f"Clearing OCR cache ({len(_ocr_cache)} results)")
        _ocr_cache = None
