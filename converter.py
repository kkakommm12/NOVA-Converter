import os
import sys
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image


# ============================================================
# NOVA — UNIVERSAL MEDIA CONVERTER
# ============================================================
import ctypes

if sys.platform.startswith("win"):
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "NOVA.UniversalMediaConverter"
    )


APP_NAME = "NOVA — Universal Media Converter"


# ============================================================
# RESOURCE PATH
# Works when running from Python AND when running as an EXE
# ============================================================
def resource_path(filename):
    if getattr(sys, "frozen", False):
        # When packaged with PyInstaller
        base_path = Path(sys.executable).resolve().parent
    else:
        # When running normally from Python
        base_path = Path(__file__).resolve().parent

    return base_path / filename

    
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm",
    ".flv", ".wmv", ".m4v", ".ts", ".mts", ".m2ts"
}

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aac", ".m4a",
    ".ogg", ".opus", ".wma", ".aiff"
}

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp",
    ".tiff", ".tif", ".ico", ".gif"
}


IMAGE_OUTPUTS = [
    "PNG",
    "JPG",
    "WEBP",
    "BMP",
    "TIFF",
    "ICO",
    "GIF"
]

VIDEO_OUTPUTS = [
    "MP4",
    "MKV",
    "MOV",
    "AVI",
    "WEBM",
    "FLV",
    "WMV",
    "M4V",
    "GIF"
]

AUDIO_OUTPUTS = [
    "MP3",
    "WAV",
    "FLAC",
    "AAC",
    "M4A",
    "OGG",
    "OPUS"
]

# Videos can become videos OR audio.
VIDEO_TARGETS = VIDEO_OUTPUTS + AUDIO_OUTPUTS


# ============================================================
# CPU WORKERS
# Leaves some logical processors free
# ============================================================

def get_worker_count():

    cpu_count = os.cpu_count() or 4

    if cpu_count <= 4:
        return 2

    return max(2, cpu_count - 2)


# ============================================================
# FIND EXECUTABLE
# ============================================================

def find_executable(name):

    if getattr(sys, "frozen", False):

        bundled = Path(sys._MEIPASS) / name

        if bundled.exists():
            return str(bundled)

    return name


FFMPEG = find_executable("ffmpeg")
FFPROBE = find_executable("ffprobe")


# ============================================================
# MAIN APP
# ============================================================

class NovaConverter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.iconbitmap(r"D:\MP3Converter\Icon.ico")


        # ----------------------------------------------------
        # WINDOW
        # ----------------------------------------------------

        self.title(APP_NAME)
        self.geometry("1100x750")

        # This is intentionally smaller than before.
        self.minsize(850, 500)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.configure(
            fg_color="#080b0a"
        )

        # ----------------------------------------------------
        # STATE
        # ----------------------------------------------------

        self.files = []
        self.converting = False
        self.output_folder = None
        self.last_output_file = None

        self.font_main = "Fredoka"
        self.worker_count = get_worker_count()

        # ----------------------------------------------------
        # ROOT GRID
        #
        # Only the queue row expands.
        #
        # 0 = Header
        # 1 = Controls
        # 2 = Queue
        # 3 = Conversion options
        # 4 = Bottom
        # ----------------------------------------------------

        self.grid_columnconfigure(
            0,
            weight=1
        )

        self.grid_rowconfigure(
            2,
            weight=1
        )

        # ----------------------------------------------------
        # BUILD UI
        # ----------------------------------------------------

        self.build_header()
        self.build_controls()
        self.build_queue()
        self.build_conversion_options()
        self.build_bottom()

        self.update_format_options()


    # ========================================================
    # HEADER
    # ========================================================

    def build_header(self):

        header = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=30,
            pady=(22, 8)
        )

        title = ctk.CTkLabel(
            header,
            text="NOVA",
            font=(self.font_main, 38, "bold"),
            text_color="#42e695"
        )

        title.pack(
            anchor="w"
        )

        subtitle = ctk.CTkLabel(
            header,
            text="UNIVERSAL MEDIA CONVERTER",
            font=(self.font_main, 14, "bold"),
            text_color="#9ca39f"
        )

        subtitle.pack(
            anchor="w"
        )


    # ========================================================
    # CONTROLS
    # ========================================================

    def build_controls(self):

        controls = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        controls.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=30,
            pady=5
        )

        self.add_files_button = ctk.CTkButton(
            controls,
            text="＋ ADD FILES",
            font=(self.font_main, 15, "bold"),
            height=42,
            corner_radius=10,
            command=self.add_files
        )

        self.add_files_button.pack(
            side="left",
            padx=(0, 10)
        )

        self.add_folder_button = ctk.CTkButton(
            controls,
            text="＋ ADD FOLDER",
            font=(self.font_main, 15, "bold"),
            height=42,
            corner_radius=10,
            command=self.add_folder
        )

        self.add_folder_button.pack(
            side="left"
        )


    # ========================================================
    # QUEUE
    # ========================================================

    def build_queue(self):

        outer = ctk.CTkFrame(
            self,
            fg_color="#0d1210",
            corner_radius=14
        )

        outer.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=30,
            pady=(15, 15)
        )

        # ----------------------------------------------------
        # QUEUE HEADER
        # ----------------------------------------------------

        top = ctk.CTkFrame(
            outer,
            fg_color="transparent"
        )

        top.pack(
            fill="x",
            padx=18,
            pady=(15, 8)
        )

        self.queue_label = ctk.CTkLabel(
            top,
            text="QUEUE • 0 FILES",
            font=(self.font_main, 15, "bold"),
            text_color="#d8dedb"
        )

        self.queue_label.pack(
            side="left"
        )

        self.clear_button = ctk.CTkButton(
            top,
            text="CLEAR",
            width=80,
            height=30,
            corner_radius=8,
            fg_color="#171d1a",
            hover_color="#252d29",
            font=(self.font_main, 12, "bold"),
            command=self.clear_files
        )

        self.clear_button.pack(
            side="right"
        )

        # ----------------------------------------------------
        # SCROLLABLE QUEUE
        # ----------------------------------------------------

        self.queue_frame = ctk.CTkScrollableFrame(
            outer,
            fg_color="transparent"
        )

        self.queue_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )


    # ========================================================
    # CONVERSION OPTIONS
    # ========================================================

    def build_conversion_options(self):

        self.options_outer = ctk.CTkFrame(
            self,
            fg_color="#0d1210",
            corner_radius=14
        )

        self.options_outer.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = ctk.CTkLabel(
            self.options_outer,
            text="CONVERSION OPTIONS",
            font=(self.font_main, 14, "bold"),
            text_color="#9ca39f"
        )

        title.pack(
            anchor="w",
            padx=18,
            pady=(13, 8)
        )

        # ----------------------------------------------------
        # ROW 0
        #
        # Pictures | Videos | Audio
        # ----------------------------------------------------

        self.options_row = ctk.CTkFrame(
            self.options_outer,
            fg_color="transparent"
        )

        self.options_row.pack(
            fill="x",
            padx=18,
            pady=(0, 8)
        )

        for column in range(3):

            self.options_row.grid_columnconfigure(
                column,
                weight=1,
                uniform="options"
            )

        # ----------------------------------------------------
        # PICTURES
        # ----------------------------------------------------

        self.image_options = ctk.CTkFrame(
            self.options_row,
            fg_color="#111713",
            corner_radius=10
        )

        self.image_title = ctk.CTkLabel(
            self.image_options,
            text="🖼  PICTURES",
            font=(self.font_main, 13, "bold"),
            text_color="#42e695"
        )

        self.image_title.pack(
            side="left",
            padx=(12, 8),
            pady=8
        )

        self.image_format = ctk.CTkComboBox(
            self.image_options,
            values=IMAGE_OUTPUTS,
            width=115,
            height=34,
            font=(self.font_main, 13),
            dropdown_font=(self.font_main, 13),
            state="readonly"
        )

        self.image_format.set("PNG")

        self.image_format.pack(
            side="left",
            padx=(0, 10),
            pady=7
        )

        # ----------------------------------------------------
        # VIDEOS
        # ----------------------------------------------------

        self.video_options = ctk.CTkFrame(
            self.options_row,
            fg_color="#111713",
            corner_radius=10
        )

        self.video_title = ctk.CTkLabel(
            self.video_options,
            text="🎬  VIDEOS",
            font=(self.font_main, 13, "bold"),
            text_color="#42e695"
        )

        self.video_title.pack(
            side="left",
            padx=(12, 8),
            pady=8
        )

        self.video_format = ctk.CTkComboBox(
            self.video_options,
            values=VIDEO_TARGETS,
            width=120,
            height=34,
            font=(self.font_main, 13),
            dropdown_font=(self.font_main, 13),
            state="readonly"
        )

        self.video_format.set("MP4")

        self.video_format.pack(
            side="left",
            padx=(0, 10),
            pady=7
        )

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        self.audio_options = ctk.CTkFrame(
            self.options_row,
            fg_color="#111713",
            corner_radius=10
        )

        self.audio_title = ctk.CTkLabel(
            self.audio_options,
            text="🎵  AUDIO",
            font=(self.font_main, 13, "bold"),
            text_color="#42e695"
        )

        self.audio_title.pack(
            side="left",
            padx=(12, 8),
            pady=8
        )

        self.audio_format = ctk.CTkComboBox(
            self.audio_options,
            values=AUDIO_OUTPUTS,
            width=115,
            height=34,
            font=(self.font_main, 13),
            dropdown_font=(self.font_main, 13),
            state="readonly"
        )

        self.audio_format.set("MP3")

        self.audio_format.pack(
            side="left",
            padx=(0, 10),
            pady=7
        )

        # ----------------------------------------------------
        # ROW 1
        #
        # Audio Quality | Output
        # ----------------------------------------------------

        self.bottom_options_row = ctk.CTkFrame(
            self.options_outer,
            fg_color="transparent"
        )

        self.bottom_options_row.pack(
            fill="x",
            padx=18,
            pady=(0, 14)
        )

        for column in range(3):

            self.bottom_options_row.grid_columnconfigure(
                column,
                weight=1,
                uniform="bottom_options"
            )

        # ----------------------------------------------------
        # AUDIO QUALITY
        # ----------------------------------------------------

        self.audio_quality_box = ctk.CTkFrame(
            self.bottom_options_row,
            fg_color="#111713",
            corner_radius=10
        )

        self.audio_quality_label = ctk.CTkLabel(
            self.audio_quality_box,
            text="AUDIO QUALITY",
            font=(self.font_main, 12, "bold"),
            text_color="#7f8984"
        )

        self.audio_quality_label.pack(
            side="left",
            padx=(12, 8),
            pady=8
        )

        self.audio_quality = ctk.CTkComboBox(
            self.audio_quality_box,
            values=[
                "128k",
                "192k",
                "256k",
                "320k"
            ],
            width=100,
            height=34,
            font=(self.font_main, 13),
            dropdown_font=(self.font_main, 13),
            state="readonly"
        )

        self.audio_quality.set("192k")

        self.audio_quality.pack(
            side="left",
            padx=(0, 10),
            pady=7
        )

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        self.output_box = ctk.CTkFrame(
            self.bottom_options_row,
            fg_color="#111713",
            corner_radius=10
        )

        self.output_label = ctk.CTkLabel(
            self.output_box,
            text="OUTPUT",
            font=(self.font_main, 12, "bold"),
            text_color="#7f8984"
        )

        self.output_label.pack(
            side="left",
            padx=(12, 8),
            pady=8
        )

        self.output_location = ctk.CTkComboBox(
            self.output_box,
            values=[
                "Same as source",
                "Choose folder..."
            ],
            width=145,
            height=34,
            font=(self.font_main, 13),
            dropdown_font=(self.font_main, 13),
            state="readonly",
            command=self.output_location_changed
        )

        self.output_location.set(
            "Same as source"
        )

        self.output_location.pack(
            side="left",
            padx=(0, 8),
            pady=7
        )

        self.browse_button = ctk.CTkButton(
            self.output_box,
            text="BROWSE",
            width=78,
            height=34,
            corner_radius=8,
            font=(self.font_main, 12, "bold"),
            command=self.choose_output_folder
        )

        self.browse_button.pack(
            side="left",
            padx=(0, 10),
            pady=7
        )


    # ========================================================
    # BOTTOM
    # ========================================================

    def build_bottom(self):

        bottom = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        bottom.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 12)
        )

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        self.progress = ctk.CTkProgressBar(
            bottom,
            height=10,
            corner_radius=5
        )

        self.progress.set(0)

        self.progress.pack(
            fill="x",
            pady=(0, 8)
        )

        # ----------------------------------------------------
        # STATUS + BUTTONS
        # ----------------------------------------------------

        status_row = ctk.CTkFrame(
            bottom,
            fg_color="transparent"
        )

        status_row.pack(
            fill="x"
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status_label = ctk.CTkLabel(
            status_row,
            text="Ready.",
            font=(self.font_main, 13),
            text_color="#9ca39f",
            anchor="w"
        )

        self.status_label.pack(
            side="left",
            fill="x",
            expand=True
        )

        # ----------------------------------------------------
        # OPEN OUTPUT
        # ----------------------------------------------------

        self.open_output_button = ctk.CTkButton(
            status_row,
            text="OPEN OUTPUT",
            width=120,
            height=34,
            corner_radius=8,
            font=(self.font_main, 12, "bold"),
            state="disabled",
            command=self.open_output
        )

        self.open_output_button.pack(
            side="right",
            padx=(10, 0)
        )

        # ----------------------------------------------------
        # CONVERT ALL
        # ----------------------------------------------------

        self.convert_button = ctk.CTkButton(
            status_row,
            text="CONVERT ALL",
            width=160,
            height=40,
            corner_radius=10,
            font=(self.font_main, 14, "bold"),
            fg_color="#20c878",
            hover_color="#19a965",
            text_color="#06100b",
            command=self.start_conversion
        )

        self.convert_button.pack(
            side="right"
        )

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = ctk.CTkLabel(
            bottom,
            text=(
                f"NOVA • Local processing • "
                f"Powered by FFmpeg + Pillow • "
                f"{self.worker_count} parallel image workers"
            ),
            font=(self.font_main, 11),
            text_color="#56615b",
            anchor="w"
        )

        footer.pack(
            anchor="w",
            pady=(5, 0)
        )


    # ========================================================
    # FILE TYPE
    # ========================================================

    def get_file_type(self, path):

        ext = Path(path).suffix.lower()

        if ext in IMAGE_EXTENSIONS:
            return "image"

        if ext in VIDEO_EXTENSIONS:
            return "video"

        if ext in AUDIO_EXTENSIONS:
            return "audio"

        return None


    # ========================================================
    # ADD FILES
    # ========================================================

    def add_files(self):

        paths = filedialog.askopenfilenames(
            title="Select media files",
            filetypes=[
                (
                    "Media files",
                    "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif *.ico *.gif "
                    "*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.m4v *.ts *.mts *.m2ts "
                    "*.mp3 *.wav *.flac *.aac *.m4a *.ogg *.opus *.wma *.aiff"
                ),
                (
                    "All files",
                    "*.*"
                )
            ]
        )

        for path in paths:
            self.add_file(path)

        self.refresh_queue()


    # ========================================================
    # ADD FOLDER
    # ========================================================

    def add_folder(self):

        folder = filedialog.askdirectory(
            title="Select media folder"
        )

        if not folder:
            return

        for root, _, filenames in os.walk(folder):

            for filename in filenames:

                path = os.path.join(
                    root,
                    filename
                )

                if self.get_file_type(path):
                    self.add_file(path)

        self.refresh_queue()


    # ========================================================
    # ADD FILE
    # ========================================================

    def add_file(self, path):

        if not os.path.isfile(path):
            return

        if not self.get_file_type(path):
            return

        if path not in self.files:
            self.files.append(path)


    # ========================================================
    # REFRESH QUEUE
    # ========================================================

    def refresh_queue(self):

        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        self.queue_label.configure(
            text=f"QUEUE • {len(self.files)} FILES"
        )

        for index, path in enumerate(self.files):

            file_type = self.get_file_type(path)

            if file_type == "image":
                icon = "🖼"

            elif file_type == "video":
                icon = "🎬"

            else:
                icon = "🎵"

            row = ctk.CTkFrame(
                self.queue_frame,
                fg_color="#111713",
                corner_radius=8,
                height=45
            )

            row.pack(
                fill="x",
                padx=5,
                pady=3
            )

            row.pack_propagate(False)

            icon_label = ctk.CTkLabel(
                row,
                text=icon,
                font=("Segoe UI Emoji", 17)
            )

            icon_label.pack(
                side="left",
                padx=(12, 8)
            )

            name_label = ctk.CTkLabel(
                row,
                text=Path(path).name,
                font=(self.font_main, 13),
                text_color="#d8dedb",
                anchor="w"
            )

            name_label.pack(
                side="left",
                fill="x",
                expand=True
            )

            ext_label = ctk.CTkLabel(
                row,
                text=Path(path).suffix.upper(),
                font=(self.font_main, 11, "bold"),
                text_color="#68736d"
            )

            ext_label.pack(
                side="left",
                padx=15
            )

            remove_button = ctk.CTkButton(
                row,
                text="×",
                width=32,
                height=30,
                corner_radius=7,
                fg_color="#191f1c",
                hover_color="#30201f",
                font=("Arial", 17, "bold"),
                command=lambda i=index: self.remove_file(i)
            )

            remove_button.pack(
                side="right",
                padx=8
            )

        self.update_format_options()


    # ========================================================
    # REMOVE
    # ========================================================

    def remove_file(self, index):

        if self.converting:
            return

        if 0 <= index < len(self.files):
            self.files.pop(index)

        self.refresh_queue()


    # ========================================================
    # CLEAR
    # ========================================================

    def clear_files(self):

        if self.converting:
            return

        self.files.clear()

        self.last_output_file = None

        self.open_output_button.configure(
            state="disabled"
        )

        self.refresh_queue()

        self.status_label.configure(
            text="Ready."
        )

        self.progress.set(0)


    # ========================================================
    # DYNAMIC OPTIONS
    # ========================================================

    def update_format_options(self):

        types = set(
            self.get_file_type(path)
            for path in self.files
        )

        # ----------------------------------------------------
        # Hide everything
        # ----------------------------------------------------

        self.image_options.grid_forget()
        self.video_options.grid_forget()
        self.audio_options.grid_forget()

        self.audio_quality_box.grid_forget()
        self.output_box.grid_forget()

        # ----------------------------------------------------
        # ROW 0
        # ----------------------------------------------------

        column = 0

        if "image" in types:

            self.image_options.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(0, 6),
                pady=(0, 8)
            )

            column += 1

        if "video" in types:

            self.video_options.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=6,
                pady=(0, 8)
            )

            column += 1

        if "audio" in types:

            self.audio_options.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(6, 0),
                pady=(0, 8)
            )

        # ----------------------------------------------------
        # ROW 1
        # ----------------------------------------------------

        column = 0

        if "audio" in types or "video" in types:

            self.audio_quality_box.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=(0, 6)
            )

            column += 1

        if types:

            self.output_box.grid(
                row=0,
                column=column,
                columnspan=max(1, 3 - column),
                sticky="ew",
                padx=(6 if column > 0 else 0, 0)
            )


    # ========================================================
    # OUTPUT LOCATION
    # ========================================================

    def output_location_changed(self, value):

        if value == "Choose folder...":
            self.choose_output_folder()


    def choose_output_folder(self):

        folder = filedialog.askdirectory(
            title="Choose output folder"
        )

        if folder:

            self.output_folder = folder

            display = folder

            if len(display) > 42:
                display = "..." + display[-39:]

            self.output_location.set(
                display
            )

        else:

            self.output_folder = None

            self.output_location.set(
                "Same as source"
            )


    # ========================================================
    # UNIQUE OUTPUT
    # ========================================================

    def unique_output(
        self,
        folder,
        stem,
        extension
    ):

        output = (
            Path(folder)
            / f"{stem}.{extension}"
        )

        counter = 1

        while output.exists():

            output = (
                Path(folder)
                / f"{stem} ({counter}).{extension}"
            )

            counter += 1

        return output


    # ========================================================
    # DETERMINE TARGET TYPE
    # ========================================================

    def get_target_type(self, output_format):

        fmt = output_format.upper()

        if fmt in IMAGE_OUTPUTS:
            return "image"

        if fmt in VIDEO_OUTPUTS:
            return "video"

        if fmt in AUDIO_OUTPUTS:
            return "audio"

        return None


    # ========================================================
    # GET OUTPUT FORMAT
    # ========================================================

    def get_output_format(self, file_type):

        if file_type == "image":
            return self.image_format.get().upper()

        if file_type == "video":
            return self.video_format.get().upper()

        if file_type == "audio":
            return self.audio_format.get().upper()

        return None


    # ========================================================
    # PREPARE JOB
    # ========================================================

    def prepare_job(self, source):

        source_type = self.get_file_type(source)

        output_format = self.get_output_format(
            source_type
        )

        if not source_type or not output_format:
            return None

        target_type = self.get_target_type(
            output_format
        )

        # ----------------------------------------------------
        # Prevent invalid conversions
        # ----------------------------------------------------

        if source_type == "image" and target_type != "image":
            return None

        if source_type == "audio" and target_type != "audio":
            return None

        source_path = Path(source)

        if self.output_folder:

            output_folder = Path(
                self.output_folder
            )

        else:

            output_folder = source_path.parent

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        output = self.unique_output(
            output_folder,
            source_path.stem,
            output_format.lower()
        )

        return {
            "source": str(source_path),
            "output": str(output),
            "source_type": source_type,
            "target_type": target_type,
            "format": output_format
        }


    # ========================================================
    # IMAGE CONVERSION
    # ========================================================

    def convert_image(
        self,
        source,
        output,
        output_format
    ):

        with Image.open(source) as img:

            if output_format == "JPG":

                if img.mode in (
                    "RGBA",
                    "LA",
                    "P"
                ):

                    if img.mode == "P":
                        img = img.convert("RGBA")

                    if img.mode in (
                        "RGBA",
                        "LA"
                    ):

                        background = Image.new(
                            "RGB",
                            img.size,
                            "white"
                        )

                        alpha = img.getchannel("A")

                        background.paste(
                            img.convert("RGB"),
                            mask=alpha
                        )

                        img = background

                else:

                    img = img.convert(
                        "RGB"
                    )

                img.save(
                    output,
                    "JPEG",
                    quality=95,
                    optimize=True
                )

            elif output_format == "PNG":

                img.save(
                    output,
                    "PNG",
                    optimize=True
                )

            elif output_format == "WEBP":

                img.save(
                    output,
                    "WEBP",
                    quality=95,
                    method=6
                )

            elif output_format == "BMP":

                img.convert(
                    "RGB"
                ).save(
                    output,
                    "BMP"
                )

            elif output_format == "TIFF":

                img.save(
                    output,
                    "TIFF"
                )

            elif output_format == "ICO":

                temp = img.convert(
                    "RGBA"
                )

                temp.thumbnail(
                    (256, 256)
                )

                temp.save(
                    output,
                    "ICO"
                )

            elif output_format == "GIF":

                if img.mode not in (
                    "P",
                    "L"
                ):

                    img = img.convert(
                        "P"
                    )

                img.save(
                    output,
                    "GIF"
                )


    # ========================================================
    # VIDEO → GIF
    # ========================================================

    def video_to_gif(
        self,
        source,
        output
    ):

        command = [
            FFMPEG,
            "-y",
            "-i",
            source,
            "-vf",
            "fps=15,scale=480:-1:flags=lanczos",
            "-loop",
            "0",
            output
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                result.stderr[-1500:]
            )


    # ========================================================
    # AUDIO ENCODING
    # ========================================================

    def build_audio_command(
        self,
        command,
        output_format
    ):

        bitrate = self.audio_quality.get()
        fmt = output_format.upper()

        if fmt == "MP3":

            command += [
                "-vn",
                "-c:a",
                "libmp3lame",
                "-b:a",
                bitrate
            ]

        elif fmt == "WAV":

            command += [
                "-vn",
                "-c:a",
                "pcm_s16le"
            ]

        elif fmt == "FLAC":

            command += [
                "-vn",
                "-c:a",
                "flac"
            ]

        elif fmt == "AAC":

            command += [
                "-vn",
                "-c:a",
                "aac",
                "-b:a",
                bitrate
            ]

        elif fmt == "M4A":

            command += [
                "-vn",
                "-c:a",
                "aac",
                "-b:a",
                bitrate
            ]

        elif fmt == "OGG":

            command += [
                "-vn",
                "-c:a",
                "libvorbis",
                "-q:a",
                "5"
            ]

        elif fmt == "OPUS":

            command += [
                "-vn",
                "-c:a",
                "libopus",
                "-b:a",
                "160k"
            ]

        return command


    # ========================================================
    # VIDEO CONVERSION
    # ========================================================

    def convert_video(
        self,
        source,
        output,
        output_format
    ):

        fmt = output_format.upper()

        # ----------------------------------------------------
        # VIDEO → AUDIO
        # ----------------------------------------------------

        if fmt in AUDIO_OUTPUTS:

            command = [
                FFMPEG,
                "-y",
                "-i",
                source
            ]

            command = self.build_audio_command(
                command,
                fmt
            )

            command.append(
                output
            )

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:

                raise RuntimeError(
                    result.stderr[-1500:]
                )

            return

        # ----------------------------------------------------
        # VIDEO → GIF
        # ----------------------------------------------------

        if fmt == "GIF":

            self.video_to_gif(
                source,
                output
            )

            return

        # ----------------------------------------------------
        # NORMAL VIDEO
        # ----------------------------------------------------

        command = [
            FFMPEG,
            "-y",
            "-i",
            source
        ]

        if fmt in (
            "MP4",
            "M4V",
            "MOV"
        ):

            command += [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "192k"
            ]

            if fmt == "MP4":

                command += [
                    "-movflags",
                    "+faststart"
                ]

        elif fmt == "MKV":

            command += [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "192k"
            ]

        elif fmt == "WEBM":

            command += [
                "-c:v",
                "libvpx-vp9",
                "-crf",
                "30",
                "-b:v",
                "0",
                "-c:a",
                "libopus",
                "-b:a",
                "128k"
            ]

        elif fmt == "AVI":

            command += [
                "-c:v",
                "mpeg4",
                "-q:v",
                "5",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k"
            ]

        elif fmt == "FLV":

            command += [
                "-c:v",
                "libx264",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "192k"
            ]

        elif fmt == "WMV":

            command += [
                "-c:v",
                "wmv2",
                "-c:a",
                "wmav2"
            ]

        command.append(
            output
        )

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                result.stderr[-1500:]
            )


    # ========================================================
    # AUDIO → AUDIO
    # ========================================================

    def convert_audio(
        self,
        source,
        output,
        output_format
    ):

        command = [
            FFMPEG,
            "-y",
            "-i",
            source
        ]

        command = self.build_audio_command(
            command,
            output_format
        )

        command.append(
            output
        )

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            raise RuntimeError(
                result.stderr[-1500:]
            )


    # ========================================================
    # CONVERT ONE
    # ========================================================

    def convert_one(self, job):

        source = job["source"]
        output = job["output"]

        source_type = job["source_type"]
        output_format = job["format"]

        if source_type == "image":

            self.convert_image(
                source,
                output,
                output_format
            )

        elif source_type == "video":

            self.convert_video(
                source,
                output,
                output_format
            )

        elif source_type == "audio":

            self.convert_audio(
                source,
                output,
                output_format
            )

        return output


    # ========================================================
    # START CONVERSION
    # ========================================================

    def start_conversion(self):

        if self.converting:
            return

        if not self.files:

            messagebox.showwarning(
                "NOVA",
                "Add some media files first."
            )

            return

        self.converting = True
        self.last_output_file = None

        self.open_output_button.configure(
            state="disabled"
        )

        self.convert_button.configure(
            state="disabled"
        )

        self.add_files_button.configure(
            state="disabled"
        )

        self.add_folder_button.configure(
            state="disabled"
        )

        self.clear_button.configure(
            state="disabled"
        )

        self.progress.set(0)

        threading.Thread(
            target=self.convert_all,
            daemon=True
        ).start()


    # ========================================================
    # CONVERT ALL
    # ========================================================

    def convert_all(self):

        jobs = []

        for source in self.files:

            try:

                job = self.prepare_job(
                    source
                )

                if job:

                    jobs.append(job)

                else:

                    print(
                        f"Skipped unsupported conversion: {source}"
                    )

            except Exception as e:

                print(
                    f"Could not prepare {source}: {e}"
                )

        total = len(jobs)

        if total == 0:

            self.after(
                0,
                lambda: self.finish_conversion(
                    0,
                    0
                )
            )

            return

        completed = 0
        success = 0
        failed = 0

        # ----------------------------------------------------
        # IMAGE JOBS
        # ----------------------------------------------------

        image_jobs = [
            job for job in jobs
            if job["source_type"] == "image"
        ]

        other_jobs = [
            job for job in jobs
            if job["source_type"] != "image"
        ]

        if image_jobs:

            workers = min(
                self.worker_count,
                len(image_jobs)
            )

            with ThreadPoolExecutor(
                max_workers=workers
            ) as executor:

                futures = {
                    executor.submit(
                        self.convert_one,
                        job
                    ): job
                    for job in image_jobs
                }

                for future in as_completed(
                    futures
                ):

                    job = futures[future]

                    try:

                        output = future.result()

                        success += 1
                        self.last_output_file = output

                    except Exception as e:

                        failed += 1

                        print(
                            f"FAILED: {job['source']}"
                        )

                        print(e)

                    completed += 1

                    self.update_progress(
                        completed,
                        total
                    )

        # ----------------------------------------------------
        # VIDEO / AUDIO
        # ----------------------------------------------------

        for job in other_jobs:

            try:

                output = self.convert_one(
                    job
                )

                success += 1
                self.last_output_file = output

            except Exception as e:

                failed += 1

                print(
                    f"FAILED: {job['source']}"
                )

                print(e)

            completed += 1

            self.update_progress(
                completed,
                total
            )

        self.after(
            0,
            lambda: self.finish_conversion(
                success,
                failed
            )
        )


    # ========================================================
    # PROGRESS
    # ========================================================

    def update_progress(
        self,
        completed,
        total
    ):

        progress = completed / total

        self.after(
            0,
            lambda p=progress,
            c=completed,
            t=total:
            self.progress_update_ui(
                p,
                c,
                t
            )
        )


    def progress_update_ui(
        self,
        progress,
        completed,
        total
    ):

        self.progress.set(
            progress
        )

        self.status_label.configure(
            text=f"Converting... {completed}/{total}"
        )


    # ========================================================
    # FINISH
    # ========================================================

    def finish_conversion(
        self,
        success,
        failed
    ):

        self.converting = False

        self.progress.set(1)

        if failed == 0:

            self.status_label.configure(
                text=(
                    f"✓ CONVERSION COMPLETE • "
                    f"{success} files"
                )
            )

        else:

            self.status_label.configure(
                text=(
                    f"✓ FINISHED • "
                    f"{success} successful • "
                    f"{failed} failed"
                )
            )

        self.convert_button.configure(
            state="normal"
        )

        self.add_files_button.configure(
            state="normal"
        )

        self.add_folder_button.configure(
            state="normal"
        )

        self.clear_button.configure(
            state="normal"
        )

        if (
            self.last_output_file
            and os.path.exists(
                self.last_output_file
            )
        ):

            self.open_output_button.configure(
                state="normal"
            )


    # ========================================================
    # OPEN OUTPUT
    # ========================================================

    def open_output(self):

        if not self.last_output_file:
            return

        output = Path(
            self.last_output_file
        )

        if not output.exists():

            messagebox.showwarning(
                "NOVA",
                "The output file no longer exists."
            )

            return

        if sys.platform.startswith("win"):

            subprocess.Popen([
                "explorer.exe",
                "/select,",
                str(output)
            ])

        elif sys.platform == "darwin":

            subprocess.Popen([
                "open",
                "-R",
                str(output)
            ])

        else:

            subprocess.Popen([
                "xdg-open",
                str(output.parent)
            ])


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app = NovaConverter()

    app.mainloop()