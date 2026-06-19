# FileTools — Setup & Run Guide
## For Pydroid 3 on Android

---

## 1. Install Dependencies

Open the **Pydroid 3 terminal** (the ≡ menu → Terminal) and run these one by one:

```bash
pip install flask
pip install Pillow
pip install PyPDF2
pip install Werkzeug
```

Or install all at once:
```bash
pip install flask Pillow PyPDF2 Werkzeug
```

**Why these libraries?**
- `flask`    — Lightweight web server, no C compiler needed
- `Pillow`   — Image processing (Pydroid 3 ships with its binary wheels)
- `PyPDF2`   — Pure-Python PDF manipulation, zero C dependencies
- `Werkzeug` — Installed automatically with Flask; handles secure filenames

---

## 2. Folder Structure

Make sure your project looks like this:

```
filetools/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
├── uploads/        ← auto-created on first run
└── outputs/        ← auto-created on first run
```

---

## 3. Run the Server

In the Pydroid 3 terminal, navigate to your project folder:

```bash
cd /sdcard/filetools       # adjust path to wherever you saved it
python app.py
```

You should see:
```
✅  FileTools server starting...
📱  Open in mobile browser: http://127.0.0.1:5000
```

---

## 4. Open in Chrome

1. Open **Google Chrome** on your phone
2. Type in the address bar: `http://127.0.0.1:5000`
3. The FileTools dashboard will load ✅

> **Tip:** Keep Pydroid 3 running in the background while you use Chrome.
> Use Android's split-screen mode if you want both visible at once.

---

## 5. How to Use

### Compress Image
1. Tap the **Compress Image** tab
2. Tap the drop zone to pick an image (or drag one in)
3. Choose output format: JPEG / PNG / WebP
4. Drag the quality slider (lower = smaller file)
5. Tap **Compress & Download** — the file saves to your Downloads folder

### Merge PDFs
1. Tap the **Merge PDF** tab
2. Tap the drop zone and select 2+ PDF files
3. Reorder or remove files using the ✕ buttons
4. Tap **Merge & Download** — the merged PDF saves to Downloads

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: flask` | Run `pip install flask` in Pydroid terminal |
| `PIL not found` | Run `pip install Pillow` |
| Browser says "Site can't be reached" | Make sure `python app.py` is still running in Pydroid |
| Port 5000 already in use | Change `port=5000` to `port=5001` in app.py and open `http://127.0.0.1:5001` |
| File won't download on Chrome | Check your browser's download permissions in Android settings |

---

## 7. Storage Note

- Uploaded files are saved temporarily to `uploads/` then immediately deleted after processing
- Output files in `outputs/` are auto-deleted after **2 minutes**
- Total disk use at any moment is less than 2× the size of your largest file
