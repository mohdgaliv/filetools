"""
FileTools - Image Compressor & PDF Merger
A lightweight Flask app built for mobile development (Pydroid 3).
Uses only standard pip-installable libraries: Flask, Pillow, PyPDF2.
"""

import os
import uuid
import threading
import time
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from PIL import Image
import PyPDF2

# ─────────────────────────────────────────────
#  App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB max upload

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR  = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR  = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "bmp", "gif"}
ALLOWED_PDF_EXTS   = {"pdf"}


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def allowed_file(filename: str, allowed: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def unique_path(folder: str, filename: str) -> str:
    """Return a unique file path inside folder."""
    name, ext = os.path.splitext(secure_filename(filename))
    unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    return os.path.join(folder, unique_name)


def schedule_delete(path: str, delay: int = 120):
    """Delete a file after `delay` seconds so temp storage stays clean."""
    def _delete():
        time.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    threading.Thread(target=_delete, daemon=True).start()


def cleanup_files(*paths):
    """Immediately delete a list of file paths (used for inputs after processing)."""
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/compress-image", methods=["POST"])
def compress_image():
    """
    Accepts: multipart/form-data
      - file   : image file
      - quality: int 1–95  (default 75)
      - format : jpeg | png | webp  (default jpeg)
    Returns: compressed image as download
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTS):
        return jsonify({"error": "Unsupported image type. Use JPG, PNG, WebP, BMP, or GIF."}), 400

    quality    = int(request.form.get("quality", 75))
    out_format = request.form.get("format", "jpeg").lower()

    # Map friendly names to Pillow format strings & MIME types
    FORMAT_MAP = {
        "jpeg": ("JPEG", "image/jpeg", ".jpg"),
        "jpg":  ("JPEG", "image/jpeg", ".jpg"),
        "png":  ("PNG",  "image/png",  ".png"),
        "webp": ("WEBP", "image/webp", ".webp"),
    }
    if out_format not in FORMAT_MAP:
        return jsonify({"error": f"Output format '{out_format}' is not supported."}), 400

    pil_format, mime_type, ext = FORMAT_MAP[out_format]

    # Save the upload temporarily
    input_path  = unique_path(UPLOAD_DIR, file.filename)
    output_name = f"compressed_{uuid.uuid4().hex[:8]}{ext}"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    try:
        file.save(input_path)

        # Open and process with Pillow
        with Image.open(input_path) as img:
            # Convert palette/RGBA images for JPEG compatibility
            if pil_format == "JPEG":
                if img.mode in ("RGBA", "P", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

            save_kwargs = {"optimize": True}
            if pil_format in ("JPEG", "WEBP"):
                save_kwargs["quality"] = max(1, min(95, quality))
            if pil_format == "PNG":
                # PNG uses compression level 0-9; map quality 1-95 → 9-0
                save_kwargs["compress_level"] = max(0, min(9, int(9 - (quality / 95) * 9)))

            img.save(output_path, format=pil_format, **save_kwargs)

        cleanup_files(input_path)
        schedule_delete(output_path, delay=120)

        original_size    = os.path.getsize(input_path) if os.path.exists(input_path) else 0
        compressed_size  = os.path.getsize(output_path)
        # input already cleaned; send size via header instead
        response = send_file(
            output_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=output_name,
        )
        response.headers["X-Compressed-Size"] = str(compressed_size)
        return response

    except Exception as e:
        cleanup_files(input_path, output_path)
        return jsonify({"error": f"Image processing failed: {str(e)}"}), 500


@app.route("/merge-pdf", methods=["POST"])
def merge_pdf():
    """
    Accepts: multipart/form-data
      - files[]: two or more PDF files
    Returns: merged PDF as download
    """
    files = request.files.getlist("files[]")
    if not files or len(files) < 2:
        return jsonify({"error": "Please upload at least 2 PDF files to merge."}), 400

    for f in files:
        if not allowed_file(f.filename, ALLOWED_PDF_EXTS):
            return jsonify({"error": f"'{f.filename}' is not a PDF. Only .pdf files are allowed."}), 400

    saved_paths = []
    output_name = f"merged_{uuid.uuid4().hex[:8]}.pdf"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    try:
        # Save all uploads
        for f in files:
            path = unique_path(UPLOAD_DIR, f.filename)
            f.save(path)
            saved_paths.append(path)

        # Merge with PyPDF2
        merger = PyPDF2.PdfMerger()
        for path in saved_paths:
            merger.append(path)
        merger.write(output_path)
        merger.close()

        cleanup_files(*saved_paths)
        schedule_delete(output_path, delay=120)

        return send_file(
            output_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=output_name,
        )

    except Exception as e:
        cleanup_files(*saved_paths, output_path)
        return jsonify({"error": f"PDF merge failed: {str(e)}"}), 500


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n✅  FileTools server starting...")
    print("📱  Open in mobile browser: http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
