# Xiaomi LSA / LSAV Media Restorer

An offline desktop GUI tool that decrypts and restores hidden `.lsa` (photos) and `.lsav` (videos) files exported from Xiaomi and POCO devices running MIUI or HyperOS.

## Overview

Photos and videos in Xiaomi's Private Album are stored in encrypted `.lsa` and `.lsav` containers. The tool attempts to restore them using the AES-128 CTR key and counter initialization values defined in the application:

- **`.lsa` (Photos):** Entire file stream is encrypted using the system gallery signature keystore.
- **`.lsav` (Videos):** Only the first 1,024 bytes (header block) are decrypted, while the remaining bytes are copied unchanged.

The tool restores files whose headers and payload are valid after decryption. It works offline and does not upload, download, or modify the original source files.

## Prerequisites

- Python 3.9+
- Compatible with Windows, macOS, and Linux

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/OsamaShamlawi/xiaomi-lsa-lsva-media-restorer.git
   cd xiaomi-lsa-lsva-media-restorer
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Graphical User Interface (GUI)

Launch the desktop application:

```bash
python decryptsvl.py
```

- Click **Browse** to select the folder containing your `.lsa` and `.lsav` files.
- Select your desired destination folder.
- Keep **Organize into 'photos' and 'videos' subfolders** checked if you want them automatically categorized.
- Click **Start Decryption**.

### 2. Standalone Windows Executable (.exe)

To compile the app into a portable Windows executable:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile decryptsvl.py
```

The compiled binary will be placed inside the `dist/` directory.

## File Organization Structure

When the sorting feature is enabled, restored items are placed into:

- `decrypted_output/photos/`: `.jpg`, `.jpeg`, `.png`, `.webp`, `.heic`
- `decrypted_output/videos/`: `.mp4`, `.mkv`, `.mov`, `.3gp`, `.webm`

## Why Some Files Fail Recovery

When the tool processes `.lsa` and `.lsav` files, it validates the file size, decrypts the payload, and checks the resulting data against known media signatures. Files that fail a check remain in the source folder; the tool does not currently create or move files into an `error` directory.

Common causes include:

### 1. File Size is 0 KB or Under 16 Bytes

The file contains zero bytes or only a few bytes of metadata or trailing data. If the original media was removed, cleared, or replaced by an incomplete placeholder, there may be no encrypted payload to recover.

### 2. Cloud-Only or Unavailable Files

The file has an `.lsa` or `.lsav` extension but contains only zeros or a placeholder instead of locally available media data. If a complete copy was never downloaded or cached, restoration is not possible.

### 3. Incomplete Transfers or Truncated Files

Interruptions during MTP or USB transfers, interrupted downloads, or copying from an unavailable file system can leave a truncated file. For videos, an incomplete stream may still be missing important container information, such as its index or metadata, even when the encrypted header can be processed.

### 4. Invalid Media Headers After Decryption

The script decrypts the file and checks for recognized media signatures. The file may fail validation if:

- It was encrypted with a different device-specific or firmware-specific key.
- It was already decrypted and is decrypted again.
- It is not a supported media file despite using an `.lsa` or `.lsav` extension.
- The source file is damaged or was copied incorrectly.

The tool uses `filetype.guess()` for format detection and checks JPEG signatures and MP4/MOV `ftyp` signatures as fallbacks.

### 5. Storage Sector Corruption or Bit Rot

A file may have a normal size while still containing corrupted or partially overwritten data. AES-CTR decryption can cause corrupted ciphertext to produce corrupted plaintext.

## Code Documentation & Breakdown

For a detailed breakdown of the functions, cryptographic cipher, UI elements, and file handlers, see [`code_explain.md`](code_explain.md).

## License

Distributed under the MIT License. See [LICENSE.md](LICENSE.md) for more information.