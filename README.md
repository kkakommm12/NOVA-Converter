# NOVA — Universal Media Converter

A free and open-source media converter for Windows.

NOVA lets you convert **video, audio, and image files** between a wide range of popular formats using a simple desktop interface.

## ✨ Features

* 🎬 Video conversion
* 🎵 Audio conversion
* 🖼️ Image conversion
* ⚡ Parallel image conversion
* 📁 Simple file queue
* 🌙 Dark interface
* 💻 Native Windows desktop application
* 🔒 Files are processed locally
* 🆓 Free and open source
* 🚫 No account required
* ☁️ No cloud upload required

## 📦 Supported Formats

### Video

Input:

* MP4
* MKV
* AVI
* MOV
* WEBM
* FLV
* WMV
* M4V
* TS
* MTS
* M2TS

Output:

* MP4
* MKV
* MOV
* AVI
* WEBM
* FLV
* WMV
* M4V
* GIF

### Audio

Input:

* MP3
* WAV
* FLAC
* AAC
* M4A
* OGG
* OPUS
* WMA
* AIFF

Output:

* MP3
* WAV
* FLAC
* AAC
* M4A
* OGG
* OPUS

### Images

Input:

* PNG
* JPG / JPEG
* WEBP
* BMP
* TIFF
* ICO
* GIF

Output:

* PNG
* JPG
* WEBP
* BMP
* TIFF
* ICO
* GIF

## 🚀 Download

Download the latest Windows release from the **Releases** section.

Extract the downloaded ZIP file and run:

`NOVA.exe`

No Python installation is required for the packaged Windows release.

## 🛠️ Running From Source

### Requirements

* Windows
* Python 3.10+
* FFmpeg
* FFprobe

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run

```bash
python converter.py
```

## 🔨 Building

NOVA can be packaged using PyInstaller.

Example:

```bash
python -m PyInstaller --noconfirm --clean --windowed --name NOVA --icon="Icon.ico" --add-data="Icon.ico;." --contents-directory "." converter.py
```

The packaged application will be created inside the `dist` directory.

## 🔐 Privacy

NOVA is designed to process your media files locally on your computer.

Your files do not need to be uploaded to a server to perform conversions.

## 📄 License

NOVA is released under the MIT License.

See [LICENSE](LICENSE) for details.

## ⚠️ Third-Party Software

NOVA uses third-party software and libraries, including:

* Python
* CustomTkinter
* Pillow
* FFmpeg
* FFprobe
* PyInstaller

Their respective licenses and terms apply.

## 🤝 Contributing

Pull requests, bug reports, and improvements are welcome.

If you find a bug or have an idea for a feature, open an issue on GitHub.

---

**NOVA — Convert your media. Keep it local.**
