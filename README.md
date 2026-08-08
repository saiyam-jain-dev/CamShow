# 🎥 CamShow - Virtual Camera Video Streamer

**CamShow** is a lightweight Windows application that loads any video file (`.mp4`, `.avi`, `.mov`, `.mkv`, etc.) and streams it as your live Virtual Camera feed into browser apps (Omegle, Chatroulette, Zoom, Discord, Google Meet, Chrome/Edge WebRTC).

---

## ✨ Features

- 💻 **Standalone Executable (`CamShow.exe`)**: Built with PyInstaller for 1-click execution.
- 🎨 **Modern Dark Mode UI**: CustomTkinter interface with live video preview canvas and playback controls.
- ⏯ **Video Controls**: Play/Pause, Seek slider, Loop toggle, time duration timestamps.
- ⚙ **Stream Quality Presets**: Original resolution, 720p (1280x720), 1080p (1920x1080), 480p (640x480).
- 🎥 **Virtual Camera Engine**: Uses OpenCV + PyVirtualCam for DirectShow virtual camera streaming on Windows.

---

## ⚡ 1-Click Installation (For Other PCs)

1. Clone or download this repository:
   ```bash
   git clone <REPO_URL>
   cd CamShow
   ```

2. Double-click **`install.bat`** (or run `install.bat` in CMD / PowerShell).
   - `install.bat` will automatically install python requirements, build `dist/CamShow.exe`, and launch the app!

---

## 🚀 How to Use on Omegle / Browsers

1. **Enable Virtual Camera in OBS Studio (One-time step)**:
   - Open OBS Studio on your PC.
   - Click **"Start Virtual Camera"** (in the bottom-right Controls dock).
   - *(This registers the Virtual Camera device in Windows so Chrome/Omegle can see it).*

2. **Stream Video with CamShow**:
   - Double-click **`dist/CamShow.exe`**.
   - Click **📂 Select Video File...** and choose your video.
   - Click **🔴 Start Broadcasting**.
   - Open Omegle in Chrome/Edge, refresh the page, and select **"OBS Virtual Camera"** from the camera dropdown list!

---

## 🛠 Manual Build Instructions

If you want to build `CamShow.exe` manually:

```bash
pip install -r requirements.txt
python build_exe.py
```

The compiled binary will be generated in `dist/CamShow.exe`.
