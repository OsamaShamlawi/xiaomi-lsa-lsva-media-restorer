# Comprehensive Line-by-Line Code Explanation

This document explains the implementation in `decryptsvl.py`.

---

## 1. Imports and Dependencies

```python
import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import filetype
from Crypto.Cipher import AES
from Crypto.Util import Counter
```

* `import os`: Provides standard operating system interfaces. Used to inspect file paths, verify existence, check file sizes, create directories, and list files.
* `import shutil`: Provides high-level file operations. Specifically used for `shutil.move()` to transfer fixed files into categorized subfolders without manual byte copying.
* `import threading`: Python's threading library. Allows running the decryption loop in a background thread so the Tkinter graphical interface doesn't freeze or show "Not Responding" during heavy I/O operations.
* `import tkinter as tk`: Python's built-in graphical user interface toolkit.
* `from tkinter import ttk, filedialog, messagebox`:
  * `ttk`: The themed widget library (native-looking buttons, progress bars, frames).
  * `filedialog`: Native folder-picker dialogs for picking input and output paths.
  * `messagebox`: Native pop-up alert dialogs (e.g., error alerts, completion notices).
* `import filetype`: Library to inspect magic bytes (file signature headers) in raw data buffers to accurately identify media formats regardless of extension.
* `from Crypto.Cipher import AES`: Imports the AES cryptographic cipher from `pycryptodome` to perform AES-128 block transformations.
* `from Crypto.Util import Counter`: Imports the stateful 128-bit counter object required for AES in Counter (CTR) mode.

---

## 2. Global Constants and Cryptographic Keys

```python
SECRET_KEY = bytes.fromhex("3082046c30820354a003020102020900")
AES_IV = 22696201676385068962342234041843478898

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".3gp", ".webm"}
```

* `SECRET_KEY = bytes.fromhex("3082046c30820354a003020102020900")`: 
  * The hardcoded 16-byte (128-bit) symmetric master key used across MIUI and HyperOS for private album media encryption.
  * `bytes.fromhex(...)` decodes the 32-character hexadecimal string into raw cryptographic bytes.
* `AES_IV = 22696201676385068962342234041843478898`:
  * The global Initialization Vector (IV) integer used by Xiaomi's gallery engine to seed the 128-bit counter for CTR mode.
* `PHOTO_EXTENSIONS`: A lookup set defining valid photo formats for post-processing organization.
* `VIDEO_EXTENSIONS`: A lookup set defining valid video formats for post-processing organization. Sets are chosen because membership tests (`in`) run in $O(1)$ constant time.

---

## 3. Class Definition and Constructor

```python
class LSADecryptorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Xiaomi LSA/LSAV Media Restorer")
        self.geometry("640x520")
        self.minsize(580, 480)
```

* `class LSADecryptorApp(tk.Tk)`: Inherits from `tk.Tk`, turning our application class into the root window itself.
* `super().__init__()`: Initializes the parent `tk.Tk` instance.
* `self.title(...)`: Sets the window title shown in the OS title bar.
* `self.geometry("640x520")`: Sets initial window width to 640px and height to 520px.
* `self.minsize(580, 480)`: Enforces the minimum resize boundaries so UI elements never collapse into each other.

```python
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.auto_sort = tk.BooleanVar(value=True)

        self._build_ui()
```

* `style = ttk.Style(self)`: Accesses the widget styling engine.
* `style.theme_use(...)`: Selects native rendering on Windows (`vista`) or clean fallback (`clam`).
* `self.input_dir = tk.StringVar()`: Reactive Tkinter string variable storing the selected source directory.
* `self.output_dir = tk.StringVar()`: Reactive Tkinter string variable storing the target export directory.
* `self.auto_sort = tk.BooleanVar(value=True)`: Reactive boolean flag tied to the sorting checkbox (defaults to checked).
* `self._build_ui()`: Method call that constructs and positions the interface widgets.

---

## 4. UI Construction (`_build_ui`)

```python
    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        folder_frame = ttk.LabelFrame(main_frame, text="Folder Setup", padding="10 10 10 10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
```

* `main_frame`: Master container with 15px internal padding, expanded across the entire window area.
* `folder_frame`: A titled border (`LabelFrame`) grouping directory paths and browse buttons together.

```python
        ttk.Label(folder_frame, text="Source Folder (Encrypted .lsa / .lsav):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(folder_frame, textvariable=self.input_dir, width=50).grid(row=1, column=0, sticky=tk.EW, padx=(0, 5), pady=2)
        ttk.Button(folder_frame, text="Browse...", command=self._browse_input).grid(row=1, column=1, pady=2)

        ttk.Label(folder_frame, text="Destination Folder (Decrypted Output):").grid(row=2, column=0, sticky=tk.W, pady=(8, 2))
        ttk.Entry(folder_frame, textvariable=self.output_dir, width=50).grid(row=3, column=0, sticky=tk.EW, padx=(0, 5), pady=2)
        ttk.Button(folder_frame, text="Browse...", command=self._browse_output).grid(row=3, column=1, pady=2)

        folder_frame.columnconfigure(0, weight=1)
```

* Labels, Entries, and Buttons for Source and Destination paths arranged on a 2D grid.
* `textvariable=...`: Two-way binds entry inputs to `self.input_dir` and `self.output_dir`.
* `command=self._browse_...`: Binds button clicks directly to dialog-handling functions.
* `folder_frame.columnconfigure(0, weight=1)`: Ensures column 0 (the text entry) expands horizontally when the window is resized.

```python
        opts_frame = ttk.Frame(main_frame)
        opts_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Checkbutton(opts_frame, text="Organize into 'photos' and 'videos' subfolders", variable=self.auto_sort).pack(side=tk.LEFT)

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(action_frame, text="Start Decryption", command=self._start_task)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.progress = ttk.Progressbar(action_frame, orient="horizontal", mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
```

* Creates the subfolder sorting checkbox.
* Builds the execution trigger button (`self.start_btn`) and the visual progress bar (`self.progress`) set to `determinate` mode so progress reflects $0 \to 100\%$.

```python
        log_frame = ttk.LabelFrame(main_frame, text="Execution Logs", padding="5 5 5 5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", height=12, state="disabled", font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scroll.set)
```

* Creates a monospace log viewer (`tk.Text`) initialized as read-only (`state="disabled"`).
* Attaches a native vertical scrollbar coupled directly to the text widget's y-view.

---

## 5. Event Callbacks & UI Helpers

```python
    def _browse_input(self):
        chosen = filedialog.askdirectory(title="Select Folder Containing .lsa / .lsav Files")
        if chosen:
            self.input_dir.set(chosen)
            if not self.output_dir.get():
                self.output_dir.set(os.path.join(chosen, "decrypted_output"))
```

* Opens a native folder-picker. If the user picks a folder, it populates `input_dir` and automatically defaults `output_dir` to a `decrypted_output` subfolder.

```python
    def _browse_output(self):
        chosen = filedialog.askdirectory(title="Select Destination Folder")
        if chosen:
            self.output_dir.set(chosen)
```

* Lets the user pick an alternative output folder.

```python
    def _log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
```

* Appends text to the log window: unlocks editing (`normal`), appends text to the end, scrolls to bottom (`see(tk.END)`), and relocks the widget (`disabled`).

---

## 6. Thread Dispatching (`_start_task`)

```python
    def _start_task(self):
        in_path = self.input_dir.get().strip()
        out_path = self.output_dir.get().strip()

        if not in_path or not os.path.exists(in_path):
            messagebox.showerror("Error", "Please select a valid source directory.")
            return

        if not out_path:
            messagebox.showerror("Error", "Please set an output directory.")
            return

        self.start_btn.config(state="disabled")
        self.progress["value"] = 0

        threading.Thread(target=self._process_files, args=(in_path, out_path), daemon=True).start()
```

* Validates that directory paths are entered and exist.
* Disables the Start button to prevent concurrent duplicate runs.
* Resets the progress bar to 0.
* Spawns a daemon worker thread targeting `_process_files`. Because it runs in a thread, the GUI remains responsive.

---

## 7. Decryption Engine & Loop (`_process_files`)

```python
    def _process_files(self, in_dir, out_dir):
        valid_exts = (".lsa", ".lsav")
        files = [f for f in os.listdir(in_dir) if f.lower().endswith(valid_exts)]

        if not files:
            self._log("No .lsa or .lsav files found in source folder.")
            self.start_btn.config(state="normal")
            return

        os.makedirs(out_dir, exist_ok=True)
        total = len(files)
        self._log(f"Found {total} files. Starting decryption...\n" + "-" * 50)

        success = 0
        failed = 0
```

* Filters directory files for `.lsa` and `.lsav` extensions.
* If empty, notifies the user and re-enables the Start button.
* Creates the target output folder if it doesn't already exist.
* Sets up running counters for successes and failures.

```python
        for idx, filename in enumerate(files, 1):
            filepath = os.path.join(in_dir, filename)
            base_name, ext = os.path.splitext(filename)
            is_video = ext.lower() == ".lsav"
```

* Iterates over all matching files with a 1-based index `idx`.
* Parses filename components and detects if the file is a video.

```python
            try:
                file_size = os.path.getsize(filepath)
                if file_size <= 16:
                    self._log(f"[-] Skipped '{filename}': File is too small to be valid.")
                    failed += 1
                    continue

                with open(filepath, "rb") as f:
                    file_bytes = f.read()
```

* Rejects files with 16 bytes or fewer because they are too small to contain a valid encrypted or media header.
* Reads the raw encrypted binary into memory.

```python
                counter = Counter.new(128, initial_value=AES_IV)
                cipher = AES.new(SECRET_KEY, mode=AES.MODE_CTR, counter=counter)
```

* Constructs a fresh 128-bit counter seeded with `AES_IV`.
* Initializes an `AES` instance in `MODE_CTR` with the static `SECRET_KEY`.

```python
                if is_video:
                    header_len = min(1024, len(file_bytes))
                    decrypted_header = cipher.decrypt(file_bytes[:header_len])
                    final_bytes = decrypted_header + file_bytes[header_len:]
                else:
                    final_bytes = cipher.decrypt(file_bytes)
```

* **Core Xiaomi Decryption Logic:**
  * For `.lsav` videos: MIUI/HyperOS only encrypts the first 1,024 bytes. Decrypting only the first 1,024 bytes and concatenating the remaining untouched bytes keeps the media container and stream valid.
  * For `.lsa` photos: The entire byte stream is encrypted; decrypts all bytes.

```python
                is_valid, detected_ext = self._detect_format(final_bytes[:1024], ext)
                if not is_valid:
                    self._log(f"[-] Failed '{filename}': Invalid header after decrypt.")
                    failed += 1
                    continue

                out_name = f"{base_name}.{detected_ext}"
                out_path = os.path.join(out_dir, out_name)
                with open(out_path, "wb") as out_f:
                    out_f.write(final_bytes)

                self._log(f"[+] Fixed: {filename} -> {out_name}")
                success += 1
```

* Passes the first 1,024 bytes of the result to `_detect_format()` to verify container integrity.
* If validation fails (bad key, corrupted download), marks as failed and continues.
* If valid, writes bytes to the destination path using the proper file extension.

```python
            except Exception as e:
                self._log(f"[!] Error on {filename}: {e}")
                failed += 1

            pct = (idx / total) * 100
            self.progress["value"] = pct
```

* Catches any file lock, OS, or permission errors without terminating the loop.
* Updates the progress bar percentage after each file.

```python
        if self.auto_sort.get() and success > 0:
            self._log("\nOrganizing media into subfolders...")
            self._sort_folders(out_dir)

        self._log("-" * 50)
        self._log(f"Finished! Successfully restored: {success} | Failed: {failed}")
        self.start_btn.config(state="normal")
        messagebox.showinfo("Done", f"Decryption complete!\n\nRestored: {success}\nFailed: {failed}")
```

* Sorts into subfolders if selected.
* Re-enables the Start button and displays a completion summary dialog box.

---

## 8. Format Detection (`_detect_format`)

```python
    def _detect_format(self, sample_bytes, source_ext):
        kind = filetype.guess(sample_bytes)
        if kind is not None:
            return True, kind.extension.lower()

        if source_ext.lower() == ".lsa" and sample_bytes.startswith(b"\xff\xd8\xff"):
            return True, "jpg"

        if source_ext.lower() == ".lsav" and len(sample_bytes) >= 12 and sample_bytes[4:8] == b"ftyp":
            return True, "mp4"

        return False, ""
```

* Checks magic bytes using `filetype.guess()`.
* Fallback checks:
  * JPEG: Bytes starting with `\xff\xd8\xff`.
  * MP4/MOV: Offset 4 through 8 matching the ISO standard `b"ftyp"` box header.
* Returns a tuple: `(True, "ext")` on success, or `(False, "")` on invalid data.

---

## 9. Media Sorting (`_sort_folders`)

```python
    def _sort_folders(self, out_dir):
        p_dir = os.path.join(out_dir, "photos")
        v_dir = os.path.join(out_dir, "videos")
        os.makedirs(p_dir, exist_ok=True)
        os.makedirs(v_dir, exist_ok=True)

        for item in os.listdir(out_dir):
            item_path = os.path.join(out_dir, item)
            if not os.path.isfile(item_path):
                continue

            _, ext = os.path.splitext(item)
            ext = ext.lower()

            if ext in PHOTO_EXTENSIONS:
                shutil.move(item_path, os.path.join(p_dir, item))
            elif ext in VIDEO_EXTENSIONS:
                shutil.move(item_path, os.path.join(v_dir, item))
```

* Creates `photos/` and `videos/` subdirectories.
* Loops through output files (skipping folders) and moves them based on their extension.

---

## 10. Application Entry Point

```python
if __name__ == "__main__":
    app = LSADecryptorApp()
    app.mainloop()
```

* Standard Python execution guard: only runs when executed directly (`python decryptsvl.py`), not when imported.
* Instantiates `LSADecryptorApp` and calls `.mainloop()` to enter Tkinter's event processing loop.