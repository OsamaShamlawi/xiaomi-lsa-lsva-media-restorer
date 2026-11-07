# Xiaomi LSA / LSAV Media Restorer

An offline desktop GUI tool and batch script to decrypt and restore hidden `.lsa` (photos) and `.lsav` (videos) files exported from Xiaomi / POCO devices running MIUI or HyperOS.

## Overview

When photos and videos are placed into Xiaomi's Private Album, they are encrypted locally using AES-128 in CTR mode:
- **`.lsa` (Photos):** Entire file stream encrypted using standard gallery keystore signatures.
- **`.lsav` (Videos):** Header-only encrypted (first 1,024 bytes) to ensure efficient media streaming.

This utility restores corrupted or orphaned files back to viewable `.jpg`, `.png`, `.mp4`, or `.mov` files without requiring an internet connection.

## Prerequisites

- Python 3.9+
- Windows, macOS, or Linux

## Installation

1. Clone this repository:
   ```bash
   git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
   cd your-repo-name

Install dependencies:

Bash
pip install -r requirements.txt
Usage
GUI Application
Launch the desktop interface:

Bash
python app.py
Select your source directory containing the .lsa and .lsav files.

Select your target export folder.

Click Start Decryption.

Build Standalone Executable (Windows)
Bash
pyinstaller --noconsole --onefile app.py
The compiled binary will be located in the dist/ directory.

License
MIT


---

### 4. `LICENSE`
Declares the open-source license for your repository.

Create a file named **`LICENSE`** (MIT License template):

```text
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.