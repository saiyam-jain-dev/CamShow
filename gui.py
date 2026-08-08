import os
import sys
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

from cam_engine import VirtualCamEngine

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CamShowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CamShow - Virtual Camera Video Streamer")
        self.geometry("900x700")
        self.minsize(800, 600)

        # Engine initialization
        self.engine = VirtualCamEngine(
            on_frame_callback=self._on_frame_update,
            on_status_change=self._on_status_update
        )

        self.current_preview_image = None
        self.is_seeking = False

        self._build_ui()
        self._start_ui_loop()

    def _build_ui(self):
        # Header Section
        self.header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E1E2E")
        self.header_frame.pack(fill="x", padx=15, pady=10)

        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="🎥 CamShow Virtual Camera", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#F5E0DC"
        )
        self.title_label.pack(side="left", padx=15, pady=10)

        self.driver_help_btn = ctk.CTkButton(
            self.header_frame,
            text="❓ Driver Setup",
            width=110,
            fg_color="#45475A",
            hover_color="#585B70",
            command=self._show_driver_help
        )
        self.driver_help_btn.pack(side="right", padx=15, pady=10)

        # Main Layout (Split View: Left Preview, Right Controls)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=5)

        # Left Column: Video Preview Panel
        self.preview_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color="#181825")
        self.preview_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="No Video Loaded\nClick 'Select Video File' to start",
            font=ctk.CTkFont(size=16),
            text_color="#A6ADC8"
        )
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Right Column: Controls Panel
        self.controls_frame = ctk.CTkFrame(self.main_container, width=320, corner_radius=10, fg_color="#1E1E2E")
        self.controls_frame.pack(side="right", fill="y", padx=5, pady=5)
        self.controls_frame.pack_propagate(False)

        # Video File Selection Button
        self.select_file_btn = ctk.CTkButton(
            self.controls_frame,
            text="📂 Select Video File...",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            fg_color="#89B4FA",
            text_color="#11111B",
            hover_color="#B4BEFE",
            command=self._browse_video
        )
        self.select_file_btn.pack(fill="x", padx=15, pady=(15, 10))

        # File Info Label
        self.file_info_label = ctk.CTkLabel(
            self.controls_frame,
            text="File: None",
            font=ctk.CTkFont(size=12),
            text_color="#BAC2DE",
            wraplength=280,
            justify="left"
        )
        self.file_info_label.pack(fill="x", padx=15, pady=2)

        self.video_stats_label = ctk.CTkLabel(
            self.controls_frame,
            text="Resolution: -- | FPS: -- | Duration: --",
            font=ctk.CTkFont(size=11),
            text_color="#A6ADC8",
            justify="left"
        )
        self.video_stats_label.pack(fill="x", padx=15, pady=2)

        # Divider
        ctk.CTkFrame(self.controls_frame, height=2, fg_color="#313244").pack(fill="x", padx=15, pady=10)

        # Broadcast Control Button (Giant Toggle)
        self.broadcast_btn = ctk.CTkButton(
            self.controls_frame,
            text="🔴 Start Broadcasting",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#A6E3A1",
            text_color="#11111B",
            hover_color="#94E2D5",
            command=self._toggle_broadcast
        )
        self.broadcast_btn.pack(fill="x", padx=15, pady=10)

        # Status Bar / Indicator
        self.status_box = ctk.CTkFrame(self.controls_frame, fg_color="#313244", corner_radius=6)
        self.status_box.pack(fill="x", padx=15, pady=5)

        self.status_indicator = ctk.CTkLabel(
            self.status_box,
            text="● OFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F38BA8"
        )
        self.status_indicator.pack(side="left", padx=10, pady=6)

        self.status_text_label = ctk.CTkLabel(
            self.status_box,
            text="Ready to stream",
            font=ctk.CTkFont(size=11),
            text_color="#CDD6F4"
        )
        self.status_text_label.pack(side="left", padx=5, pady=6, fill="x", expand=True)

        # Divider
        ctk.CTkFrame(self.controls_frame, height=2, fg_color="#313244").pack(fill="x", padx=15, pady=10)

        # Playback Controls (Play/Pause, Loop)
        self.play_pause_btn = ctk.CTkButton(
            self.controls_frame,
            text="⏸ Pause Video",
            height=35,
            fg_color="#45475A",
            hover_color="#585B70",
            command=self._toggle_play_pause
        )
        self.play_pause_btn.pack(fill="x", padx=15, pady=5)

        self.loop_switch = ctk.CTkSwitch(
            self.controls_frame,
            text="Loop Video Continuously",
            font=ctk.CTkFont(size=13),
            command=self._toggle_loop
        )
        self.loop_switch.pack(anchor="w", padx=15, pady=10)
        self.loop_switch.select()

        # Resolution preset options
        self.res_label = ctk.CTkLabel(self.controls_frame, text="Target Stream Resolution:", font=ctk.CTkFont(size=12))
        self.res_label.pack(anchor="w", padx=15, pady=(5, 2))

        self.res_option = ctk.CTkOptionMenu(
            self.controls_frame,
            values=["Original (Auto)", "1280x720 (720p)", "1920x1080 (1080p)", "640x480 (SD)"],
            fg_color="#313244",
            button_color="#45475A",
            command=self._on_res_change
        )
        self.res_option.pack(fill="x", padx=15, pady=5)

        # Timeline Seek Bar Section at bottom of app
        self.timeline_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E1E2E")
        self.timeline_frame.pack(fill="x", padx=15, pady=(5, 15))

        self.time_label = ctk.CTkLabel(
            self.timeline_frame, 
            text="00:00 / 00:00", 
            font=ctk.CTkFont(size=12),
            text_color="#BAC2DE"
        )
        self.time_label.pack(side="left", padx=15, pady=8)

        self.seek_slider = ctk.CTkSlider(
            self.timeline_frame,
            from_=0,
            to=100,
            command=self._on_seek_drag
        )
        self.seek_slider.pack(side="right", fill="x", expand=True, padx=(5, 15), pady=8)
        self.seek_slider.set(0)

    def _browse_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"), ("All Files", "*.*")]
        )
        if file_path:
            success = self.engine.load_video(file_path)
            if success:
                filename = os.path.basename(file_path)
                self.file_info_label.configure(text=f"File: {filename}")
                dur_str = self._format_time(self.engine.duration)
                self.video_stats_label.configure(
                    text=f"Resolution: {self.engine.width}x{self.engine.height} | FPS: {self.engine.fps:.1f} | Duration: {dur_str}"
                )
                self.seek_slider.configure(to=max(1, self.engine.total_frames - 1))
                self.seek_slider.set(0)
                self.time_label.configure(text=f"00:00 / {dur_str}")
            else:
                messagebox.showerror("Error Opening Video", self.engine.last_error_msg)

    def _toggle_broadcast(self):
        if not self.engine.is_streaming:
            opt = self.res_option.get()
            target_w, target_h = None, None
            if "1280x720" in opt:
                target_w, target_h = 1280, 720
            elif "1920x1080" in opt:
                target_w, target_h = 1920, 1080
            elif "640x480" in opt:
                target_w, target_h = 640, 480

            success = self.engine.start_stream(target_w, target_h)
            if success:
                self.broadcast_btn.configure(text="⬛ Stop Broadcasting", fg_color="#F38BA8", hover_color="#EBA0AC")
            else:
                self._show_missing_driver_dialog(self.engine.last_error_msg)
        else:
            self.engine.stop_stream()
            self.broadcast_btn.configure(text="🔴 Start Broadcasting", fg_color="#A6E3A1", hover_color="#94E2D5")

    def _show_missing_driver_dialog(self, error_details: str):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Virtual Camera Driver Required")
        dlg.geometry("520x360")
        dlg.attributes("-topmost", True)
        dlg.resizable(False, False)

        title = ctk.CTkLabel(
            dlg, 
            text="⚠️ Virtual Camera Driver Needed", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F38BA8"
        )
        title.pack(padx=20, pady=(15, 5))

        msg = (
            "Windows requires a Virtual Camera driver (DirectShow filter) so browsers\n"
            "(Omegle, Chrome, Zoom) can see your uploaded video as a physical webcam.\n\n"
            "Quick Fix (Free):\n"
            "Install OBS Studio. It automatically registers 'OBS Virtual Camera' on Windows."
        )
        txt = ctk.CTkLabel(dlg, text=msg, font=ctk.CTkFont(size=13), justify="center", text_color="#CDD6F4")
        txt.pack(padx=20, pady=10)

        # Download OBS Studio button
        btn_obs = ctk.CTkButton(
            dlg,
            text="🌐 Download Free OBS Studio (https://obsproject.com)",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#89B4FA",
            text_color="#11111B",
            hover_color="#B4BEFE",
            command=lambda: webbrowser.open("https://obsproject.com")
        )
        btn_obs.pack(fill="x", padx=30, pady=10)

        btn_close = ctk.CTkButton(
            dlg,
            text="Close",
            width=100,
            fg_color="#45475A",
            hover_color="#585B70",
            command=dlg.destroy
        )
        btn_close.pack(pady=10)

    def _toggle_play_pause(self):
        is_paused = self.engine.toggle_pause()
        if is_paused:
            self.play_pause_btn.configure(text="▶ Play Video")
        else:
            self.play_pause_btn.configure(text="⏸ Pause Video")

    def _toggle_loop(self):
        self.engine.loop = bool(self.loop_switch.get())

    def _on_res_change(self, choice):
        if self.engine.is_streaming:
            self.engine.stop_stream()
            self._toggle_broadcast()

    def _on_seek_drag(self, value):
        if self.engine.total_frames > 0:
            frame_idx = int(value)
            self.engine.seek(frame_idx)

    def _on_frame_update(self, rgb_frame: np.ndarray):
        """Callback invoked when a new frame is read. Updates preview image label on GUI thread."""
        try:
            w = max(100, self.preview_frame.winfo_width() - 20)
            h = max(100, self.preview_frame.winfo_height() - 20)
            
            img_h, img_w = rgb_frame.shape[:2]
            scale = min(w / img_w, h / img_h)
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))

            pil_img = Image.fromarray(rgb_frame).resize((new_w, new_h), Image.Resampling.BILINEAR)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(new_w, new_h))

            self.after(0, self._update_preview_widget, ctk_img)
        except Exception:
            pass

    def _update_preview_widget(self, ctk_img):
        self.preview_label.configure(image=ctk_img, text="")
        self.preview_label.image = ctk_img

    def _on_status_update(self, msg: str, active: bool):
        self.after(0, self._update_status_ui, msg, active)

    def _update_status_ui(self, msg: str, active: bool):
        if active:
            self.status_indicator.configure(text="● LIVE", text_color="#A6E3A1")
            self.status_text_label.configure(text=msg)
            self.broadcast_btn.configure(text="⬛ Stop Broadcasting", fg_color="#F38BA8", hover_color="#EBA0AC")
        else:
            self.status_indicator.configure(text="● OFF", text_color="#F38BA8")
            self.status_text_label.configure(text=msg)
            self.broadcast_btn.configure(text="🔴 Start Broadcasting", fg_color="#A6E3A1", hover_color="#94E2D5")

    def _start_ui_loop(self):
        """Periodic timer to update timeline seek slider and timestamp."""
        if self.engine.is_streaming or self.engine.cap:
            curr_sec = self.engine.get_progress_seconds()
            dur_sec = self.engine.duration
            self.time_label.configure(text=f"{self._format_time(curr_sec)} / {self._format_time(dur_sec)}")
            if not self.is_seeking and self.engine.total_frames > 0:
                self.seek_slider.set(self.engine.current_frame_idx)
        self.after(200, self._start_ui_loop)

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def _show_driver_help(self):
        self._show_missing_driver_dialog("")

    def on_closing(self):
        self.engine.stop_stream()
        self.destroy()

if __name__ == "__main__":
    app = CamShowApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
