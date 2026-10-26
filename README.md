# MsmLogo 🚀
### Linux Boot Logo Manager & Creator (Plymouth & GRUB)

**MsmLogo** is a lightweight, modern, and user-friendly Linux desktop utility designed to create, customize, and apply **Plymouth Boot Animations** and **GRUB Bootloader Backgrounds** with **1-Click** privilege escalation—without touching the terminal.

---

## 🌟 Features & Highlights

### 🎨 1. Logo & Text Editor (Create Mode)
- **Custom Image Upload**: Import custom vector icons or raster graphics (`.png`, `.svg`, `.jpg`, `.webp`).
- **Typography & Font Selector**: Customize OS Name, Tagline, or personal branding. Choose from system fonts, adjust font size, weight (Bold/Regular), letter spacing, text offsets, and luminous text glow.
- **Aspect Ratio & Resolution**: Tailor animations for **1080p Full HD (1920x1080)**, **4K UHD (3840x2160)**, **720p HD (1280x720)**, or custom resolutions.
- **Background Engine**:
  - Radial Spotlight Vignette
  - Vertical Linear Gradient
  - Solid Color
  - Custom Wallpaper Background Image
- **GRUB Bootloader Sync**: Automatically generates a matching GRUB background and registers it with `update-grub`.

### ✨ 2. Animation & Visual Effects Engine
- **Shimmer Sweep Effect**: Luminous, metallic light reflection sweeping diagonally across your emblem and text with customizable angle, beam width, intensity, and speed.
- **Pulse Glow Aura**: Breathing radial glow expanding and contracting rhythmically around the logo.
- **Boot Spinner / Throbber**:
  - Sleek Arc (Ubuntu style)
  - Orbiting Dots (Mint style)
  - Segmented Ring
  - Dual Counter-Rotating Rings
- **Motion & Transitions**:
  - Breathing pulse scale effect
  - Smooth Alpha Fade-in and Fade-out transitions
- **Frame Rate & Speed Controller**:
  - Configurable FPS (15, 24, 30, 60 FPS)
  - Configurable loop duration (2.0s, 3.0s, 4.0s, 5.0s)
  - Automatic frame count calculation and memory-efficient rendering.

### 🖥️ 3. Real-Time Live Preview Panel
- **Real-Time Simulation**: Simulates the exact boot screen experience at 30/60 FPS.
- **Timeline Scrubber**: Play, pause, rewind, and scrub through individual animation frames.
- **Kernel Boot Log Simulation (F2 / Esc)**: Overlay simulated systemd kernel startup messages to see how the logo looks when boot details are triggered.
- **GRUB Menu Simulation**: Toggle a simulated GRUB 2.0 menu to preview bootloader styling.
- **Fullscreen Preview**: Test the boot animation in borderless fullscreen mode (press `ESC` or `Q` to exit).

### ⚡ 4. 1-Click Theme Installer & Manager
- **1-Click Apply**: Renders PNG sequence and uses `pkexec` (Polkit GUI prompt) to:
  1. Install theme into `/usr/share/plymouth/themes/<theme_name>/`
  2. Register theme in `update-alternatives`
  3. Set theme as system default
  4. Sync GRUB background (`/etc/default/grub.d/99_msmlogo.cfg`)
  5. Execute `update-initramfs -u` with live terminal streaming in the GUI.
- **Active Themes Manager**: Lists all installed Plymouth themes, shows active status, and enables 1-click switching.
- **Backup & Restore**: Automatically preserves the original factory boot theme and provides a 1-click restore button.
- **Theme Archive Export & Import**: Share or backup creations as `.msmtheme` / `.tar.gz` packages.

### 📦 5. Ready-Made Preset Templates
1. **Cyberpunk Neon Pulse**: Deep dark vignette, electric cyan and pink neon glow, dual-ring spinner, and high-tech typography.
2. **Linux Mint Modern Glow**: Sleek Linux Mint branding, soft emerald glow aura, orbiting dots spinner, and silver shimmer sweep.
3. **Ubuntu Cosmic Aurora**: Aubergine backdrop, warm orange radiant glow, sleek circular arc, and elegant typography.
4. **Minimal Power Shimmer**: Indigo power ring emblem, clean radial dark background, and metallic shimmer sweep.

---

## 🏗️ Architecture & Workflow

```plaintext
[User GUI Input] 
       │
       ▼
[Design & Animation Editor] (Qt6 / Pillow / Cairo)
       │
       ▼
[Frame Sequence & Script Generator] (animation-0001.png ... 0090.png + .plymouth descriptor)
       │
       ▼
[Apply Button Click] ──▶ [pkexec (Polkit GUI Password Prompt)]
                                    │
                                    ▼
       ┌────────────────────────────┴────────────────────────────┐
       ▼                                                         ▼
[update-alternatives --install & --set]              [update-grub (optional)]
       │                                                         │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
                        [update-initramfs -u]
                                    │
                                    ▼
                       [New Boot Theme Active! 🎉]
```

---

## 💻 Installation & Usage

### Prerequisites
- Linux OS: Ubuntu, Linux Mint, Debian, or derivative.
- Python 3.10+
- Plymouth (`plymouth`, `update-initramfs`)

### Quick Start
To launch the application:
```bash
./run.sh
```
Or directly with Python:
```bash
python3 msmlogo/main.py
```

### Install Desktop Launcher
To add MsmLogo to your Linux Application Menu:
```bash
cp msmlogo.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
```

---

## 📁 Project Structure

```
msmlogo/
├── assets/
│   ├── icons/            # App icons (SVG and PNG)
│   └── samples/          # Built-in sample emblems (Mint, Ubuntu, Cyber, Power)
├── msmlogo/
│   ├── __init__.py
│   ├── main.py           # Application entrypoint
│   ├── core/
│   │   ├── models.py     # Data models & JSON serialization
│   │   ├── renderer.py   # High-performance frame rendering engine
│   │   ├── templates.py  # Ready-to-edit preset templates
│   │   ├── plymouth_generator.py # Generates Plymouth theme folders & assets
│   │   └── system_manager.py     # Theme discovery & pkexec execution
│   ├── backend/
│   │   └── apply_helper.py       # Root helper script executed via pkexec
│   ├── data/
│   │   └── org.msmlogo.policy   # Polkit privilege policy
│   └── ui/
│       ├── main_window.py        # Central application layout
│       ├── preview_canvas.py     # Real-time boot preview monitor & controls
│       ├── editor_tab.py         # Logo, text, and canvas properties editor
│       ├── effects_tab.py        # Shimmer, glow, spinner & timing controls
│       ├── presets_tab.py        # Ready-made template gallery
│       ├── themes_manager_tab.py # System themes manager & switch/restore
│       ├── apply_dialog.py       # 1-Click install dialog with live console
│       └── styles.py             # Dark modern theme stylesheet
├── tests/
│   ├── test_renderer.py          # Unit tests for rendering & models
│   └── test_plymouth_generator.py# Unit tests for theme generation & discovery
├── msmlogo.desktop
├── run.sh
└── setup.py
```

---

## 🛡️ Privilege Separation & Safety
- **No root GUI**: The GUI runs under the regular user account for security and Wayland/X11 compatibility.
- **Isolated Helper**: Privilege escalation only happens when executing system tasks via `pkexec`.
- **Automatic Factory Backup**: The initial system boot configuration is safely archived in `/etc/msmlogo_backup.json` so you can revert anytime with 1-click.

---

## 📦 Building & Installing Debian (.deb) Package

To build the standalone `.deb` package on Ubuntu, Debian, or Linux Mint:

```bash
./build_deb.sh
```

The output package will be generated at:
```
dist/msmlogo_1.0.0_amd64.deb
```

### Install with apt:
```bash
sudo apt install ./dist/msmlogo_1.0.0_amd64.deb
```

### Launching:
- From the system application menu: Search for **MsmLogo**
- From terminal: Run `msmlogo`

