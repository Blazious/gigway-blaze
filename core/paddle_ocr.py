import os
from paddleocr import PaddleOCR
try:
    # draw_ocr location can vary between versions
    from paddleocr import draw_ocr
except Exception:
    try:
        from paddleocr.tools import draw_ocr
    except Exception:
        draw_ocr = None
from PIL import Image


def ocr_image(image_path: str, use_gpu: bool = False, lang: str = "en"):
    """Run PaddleOCR on an image and return the extracted text and raw result.

    Args:
        image_path: Path to the image file.
        use_gpu: Whether to enable GPU (if available).
        lang: Language model to use (e.g., "en").

    Returns:
        A tuple (text, raw_result) where text is a newline-joined string of OCR lines.
    """
    # Optionally disable the model source check if network or host checks fail
    # e.g. set PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True in the environment
    if os.getenv("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "False").lower() in ("1", "true", "yes"):
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

    # PaddleOCR constructor signature varies across versions and some
    # builds don't accept `use_gpu` as a kwarg. Try a few safe argument
    # combinations and fall back to the simplest constructor.
    def _make_ocr():
        base_kwargs = {"lang": lang}
        candidates = [
            {"use_textline_orientation": True, **base_kwargs},
            {"use_angle_cls": True, **base_kwargs},
            base_kwargs,
        ]
        last_exc = None
        for kw in candidates:
            try:
                return PaddleOCR(**kw)
            except (TypeError, ValueError) as exc:
                last_exc = exc
                continue
        # If none worked, raise the last exception for visibility
        if last_exc:
            raise last_exc

    ocr = _make_ocr()
    # `ocr.ocr` signature also differs; prefer `cls=True` but fall back if it errors
    try:
        result = ocr.ocr(image_path, cls=True)
    except TypeError:
        result = ocr.ocr(image_path)

    lines = []
    for block in result:
        # Each block is usually a list of detected lines
        if isinstance(block, list):
            for line in block:
                # line format: [box, (text, confidence)]
                text = line[1][0]
                lines.append(text)
        else:
            # Fallback if structure differs
            try:
                text = block[1][0]
                lines.append(text)
            except Exception:
                continue

    return "\n".join(lines), result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run PaddleOCR on an image")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--gpu", action="store_true", help="Enable GPU if available")
    parser.add_argument("--lang", default="en", help="Language model to use (default: en)")
    args = parser.parse_args()

    text, raw = ocr_image(args.image, use_gpu=args.gpu, lang=args.lang)
    print("--- OCR Output ---")
    print(text)