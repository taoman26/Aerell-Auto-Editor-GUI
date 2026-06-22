# Aerell Auto Editor GUI

Aerell Auto Editor GUI is a graphical user interface (GUI) application designed to simplify video editing using the powerful [Auto-Editor](https://github.com/WyattBlue/auto-editor) tool by WyattBlue.

Built with **PySide6**, this application provides an intuitive interface for users who prefer visual controls over command-line operations. It can be compiled into a standalone executable using **Nuitka**, making it easy to distribute and run without requiring a Python environment.

## Features
- User-friendly GUI for Auto-Editor
- Built with PySide6 for native look and feel
- Pre-configured with `pyproject.toml` and `uv.lock` for reliable dependency management
- Standalone executable build support via Nuitka (Windows-ready with `build.cmd`)
- Inspired by [auto-editor-gui](https://github.com/sashminea/auto-editor-gui) by sashminea
- **Multiple file input** – import several video/audio files at once and reorder them via ↑/↓ buttons before processing
- **Silent Cut** – adjustable audio threshold for silence-based cutting (`--edit audio:threshold`)
- **Motion Cut** – optional motion-based cutting with adjustable threshold (`--edit motion:threshold`)
- **Margin** – configurable padding in seconds kept around each detected edit point (`--margin`)
- **Live output log** – real-time display of Auto-Editor's output during processing, with a clear "Done." or "Failed" message on completion

## Requirements
- [Python](https://www.python.org/downloads/) (recommended: 3.12)
- [uv](https://github.com/astral-sh/uv) – Fast Python package installer and resolver
- Windows (for pre-built `build.cmd`; Linux/macOS users can create custom build scripts)

### Linux(Ubuntu) additional dependency
PySide6 6.5+ requires `libxcb-cursor0`. Install it before running:
```bash
sudo apt-get install libxcb-cursor0
```

## Installation
This project uses `uv` for virtual environment and dependency management.

1. **Create virtual environment and install dependencies**:
   ```bash
   uv sync
   ```
   > This will create a virtual environment and install all required packages based on `pyproject.toml` and `uv.lock`.

3. Activate the virtual environment:
   - On Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - On Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```

## Usage
After installation, run the application using one of the following methods:

**Option A – with `uv run` (no activation needed):**
```bash
uv run -m aerell_auto_editor_gui
```

**Option B – with the virtual environment activated:**
```bash
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

python -m aerell_auto_editor_gui
```

Use the GUI to:
- Import one or more video/audio files (mp4, mov, m4a) and arrange their order with the ↑/↓ buttons
- Configure editing options:
  - **Export** – choose the output format (default: none, i.e. standard video output)
  - **Silent Cut** – enable and tune the audio silence threshold (0.00–1.00, default 0.04)
  - **Motion Cut** – optionally enable motion-based cutting with its own threshold (0.00–1.00, default 0.02)
  - **Margin** – set how many seconds of context to keep around each cut point (default 0.2 sec)
- Click **Execute** and watch Auto-Editor’s progress in the live output log below the button
- When finished, the log shows **Done.** on success or **Failed (exit code: N)** on error

## Building Standalone Executable (Windows)
A pre-made build script is included for Windows users.

1. Run the batch script:
   ```cmd
   build.cmd
   ```
   
2. An executable file will be created in a new folder that will appear in the root folder with the name `aerell-auto-editor-gui.exe`.

> **Note for Linux/macOS users**: The `build.cmd` script is Windows-specific. You can create your own build script using a similar Nuitka command (adjust paths and flags as needed).

## Credits
- [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) – Core video/audio editing engine
- [sashminea/auto-editor-gui](https://github.com/sashminea/auto-editor-gui) – GUI inspiration
- [Astral.sh uv](https://github.com/astral-sh/uv) – Modern Python packaging
- **Aerell** – Developer of this GUI adaptation
- **Michihiko Mikami** – Additional features and modifications

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
