import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import filetype
from Crypto.Cipher import AES
from Crypto.Util import Counter

# Standard Global MIUI / HyperOS Gallery key & IV
SECRET_KEY = bytes.fromhex("3082046c30820354a003020102020900")
AES_IV = 22696201676385068962342234041843478898

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".3gp", ".webm"}


class LSADecryptorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Xiaomi LSA/LSAV Media Restorer")
        self.geometry("640x520")
        self.minsize(580, 480)

        # Apply a clean theme
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.auto_sort = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Folder pickers frame
        folder_frame = ttk.LabelFrame(main_frame, text="Folder Setup", padding="10 10 10 10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        # Input Directory
        ttk.Label(folder_frame, text="Source Folder (Encrypted .lsa / .lsav):").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(folder_frame, textvariable=self.input_dir, width=50).grid(row=1, column=0, sticky=tk.EW, padx=(0, 5), pady=2)
        ttk.Button(folder_frame, text="Browse...", command=self._browse_input).grid(row=1, column=1, pady=2)

        # Output Directory
        ttk.Label(folder_frame, text="Destination Folder (Decrypted Output):").grid(row=2, column=0, sticky=tk.W, pady=(8, 2))
        ttk.Entry(folder_frame, textvariable=self.output_dir, width=50).grid(row=3, column=0, sticky=tk.EW, padx=(0, 5), pady=2)
        ttk.Button(folder_frame, text="Browse...", command=self._browse_output).grid(row=3, column=1, pady=2)

        folder_frame.columnconfigure(0, weight=1)

        # Options Frame
        opts_frame = ttk.Frame(main_frame)
        opts_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Checkbutton(opts_frame, text="Organize into 'photos' and 'videos' subfolders", variable=self.auto_sort).pack(side=tk.LEFT)

        # Start Button & Progress
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(action_frame, text="Start Decryption", command=self._start_task)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.progress = ttk.Progressbar(action_frame, orient="horizontal", mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Log Window
        log_frame = ttk.LabelFrame(main_frame, text="Execution Logs", padding="5 5 5 5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", height=12, state="disabled", font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scroll.set)

    def _browse_input(self):
        chosen = filedialog.askdirectory(title="Select Folder Containing .lsa / .lsav Files")
        if chosen:
            self.input_dir.set(chosen)
            if not self.output_dir.get():
                self.output_dir.set(os.path.join(chosen, "decrypted_output"))

    def _browse_output(self):
        chosen = filedialog.askdirectory(title="Select Destination Folder")
        if chosen:
            self.output_dir.set(chosen)

    def _log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

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

        # Run process in a separate background thread to keep UI responsive
        threading.Thread(target=self._process_files, args=(in_path, out_path), daemon=True).start()

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

        for idx, filename in enumerate(files, 1):
            filepath = os.path.join(in_dir, filename)
            base_name, ext = os.path.splitext(filename)
            is_video = ext.lower() == ".lsav"

            try:
                file_size = os.path.getsize(filepath)
                if file_size <= 16:
                    self._log(f"[-] Skipped '{filename}': File is empty (0 KB).")
                    failed += 1
                    continue

                with open(filepath, "rb") as f:
                    file_bytes = f.read()

                # AES-CTR Cipher initialization
                counter = Counter.new(128, initial_value=AES_IV)
                cipher = AES.new(SECRET_KEY, mode=AES.MODE_CTR, counter=counter)

                # Decrypt full file for photos, header only (1024 bytes) for videos
                if is_video:
                    header_len = min(1024, len(file_bytes))
                    decrypted_header = cipher.decrypt(file_bytes[:header_len])
                    final_bytes = decrypted_header + file_bytes[header_len:]
                else:
                    final_bytes = cipher.decrypt(file_bytes)

                # Validate header
                is_valid, detected_ext = self._detect_format(final_bytes[:1024], ext)
                if not is_valid:
                    self._log(f"[-] Failed '{filename}': Invalid header after decrypt.")
                    failed += 1
                    continue

                # Save file
                out_name = f"{base_name}.{detected_ext}"
                out_path = os.path.join(out_dir, out_name)
                with open(out_path, "wb") as out_f:
                    out_f.write(final_bytes)

                self._log(f"[+] Fixed: {filename} -> {out_name}")
                success += 1

            except Exception as e:
                self._log(f"[!] Error on {filename}: {e}")
                failed += 1

            # Update progress bar
            pct = (idx / total) * 100
            self.progress["value"] = pct

        # Sort files if checked
        if self.auto_sort.get() and success > 0:
            self._log("\nOrganizing media into subfolders...")
            self._sort_folders(out_dir)

        self._log("-" * 50)
        self._log(f"Finished! Successfully restored: {success} | Failed: {failed}")
        self.start_btn.config(state="normal")
        messagebox.showinfo("Done", f"Decryption complete!\n\nRestored: {success}\nFailed: {failed}")

    def _detect_format(self, sample_bytes, source_ext):
        kind = filetype.guess(sample_bytes)
        if kind is not None:
            return True, kind.extension.lower()

        # JPEG fallback
        if source_ext.lower() == ".lsa" and sample_bytes.startswith(b"\xff\xd8\xff"):
            return True, "jpg"

        # MP4 fallback
        if source_ext.lower() == ".lsav" and len(sample_bytes) >= 12 and sample_bytes[4:8] == b"ftyp":
            return True, "mp4"

        return False, ""

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


if __name__ == "__main__":
    app = LSADecryptorApp()
    app.mainloop()