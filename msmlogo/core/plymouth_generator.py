"""Plymouth theme package generator and asset builder."""

import os
import shutil
import json
from typing import Callable, Optional
from PIL import Image
from .models import ThemeProject
from .renderer import BootRenderer


class PlymouthGenerator:
    def __init__(self, project: ThemeProject):
        self.project = project
        self.renderer = BootRenderer(project)

    def generate_theme(self, output_dir: str, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> str:
        """Renders optimized assets and builds a high-performance Plymouth theme folder."""
        theme_name = self.project.name.strip().replace(" ", "-").lower()
        if not theme_name.startswith("msm-"):
            theme_name = f"msm-{theme_name}"

        theme_dir = os.path.join(output_dir, theme_name)
        os.makedirs(theme_dir, exist_ok=True)

        total_frames = self.project.total_frames
        if progress_callback:
            progress_callback(0, total_frames, "Initializing high-performance renderer...")

        w, h = self.project.width, self.project.height

        # Determine effective Plymouth module:
        # Dynamic effects (shimmer sweep, glow pulse, breathe zoom) require the script engine
        # for fluid unthrottled timer-based animation without two-step progress stalls.
        has_dynamic_effects = (
            self.project.effects.shimmer_enabled
            or self.project.effects.glow_pulse_enabled
            or self.project.effects.zoom_effect in ["breathe", "zoom_in"]
        )

        effective_module = self.project.plymouth_module or ("script" if has_dynamic_effects else "two-step")
        if effective_module == "auto":
            effective_module = "script" if has_dynamic_effects else "two-step"

        # 1. Save static background image (drawn once, zero per-frame blit overhead)
        bg_img = self.renderer.get_background(w, h)
        bg_img.save(os.path.join(theme_dir, "background.png"), "PNG")
        bg_img.save(os.path.join(theme_dir, "grub-background.png"), "PNG")

        preview_frame_idx = max(0, int(total_frames * 0.35))

        offset_x, offset_y = 0, 0

        if effective_module == "script":
            # SCRIPT MODE: Optimized layered sprite animation.
            # Crop foreground elements tightly to unified bounding box (e.g. 400x450 instead of 1920x1080).
            # This reduces per-frame RAM & GPU bus transfer from 8.3 MB down to ~600 KB (14x lighter!).
            bbox = self.renderer.get_unified_foreground_bbox(w, h)
            bx0, by0, bx1, by1 = bbox
            bw, bh = bx1 - bx0, by1 - by0

            # Calculate content offset relative to screen center
            offset_x = int((bx0 + bw / 2) - (w / 2))
            offset_y = int((by0 + bh / 2) - (h / 2))

            for idx in range(total_frames):
                frame_num = idx + 1
                frame_filename = f"animation-{frame_num:04d}.png"
                frame_path = os.path.join(theme_dir, frame_filename)

                # Render transparent foreground and crop to unified bbox
                fg = self.renderer.render_foreground_frame(idx, w, h)
                cropped = fg.crop(bbox)
                cropped.save(frame_path, "PNG", optimize=True)

                if idx == preview_frame_idx:
                    # Compose preview onto background
                    preview_comp = bg_img.copy()
                    preview_comp.alpha_composite(cropped, (bx0, by0))
                    preview_path = os.path.join(theme_dir, "preview.png")
                    preview_comp.resize((480, 270), Image.Resampling.LANCZOS).save(preview_path, "PNG")

                if progress_callback:
                    progress_callback(idx + 1, total_frames, f"Rendering optimized frame {frame_num}/{total_frames}...")

            # Also generate isolated throbber frames for fallback
            total_throbber = min(30, max(1, total_frames))
            for t_idx in range(1, total_throbber + 1):
                throbber_file = os.path.join(theme_dir, f"throbber-{t_idx:04d}.png")
                spin_img = self.renderer.render_isolated_spinner_frame(t_idx - 1, total_frames=total_throbber)
                if spin_img is not None:
                    spin_img.save(throbber_file, "PNG", optimize=True)
                else:
                    # Fallback to copy animation frame
                    src_frame = os.path.join(theme_dir, f"animation-{t_idx:04d}.png")
                    if os.path.exists(src_frame):
                        shutil.copyfile(src_frame, throbber_file)

        else:
            # TWO-STEP MODE: Official distribution standard (Mint / Ubuntu stock architecture).
            # 1. Static emblem (bgrt-fallback.png and header-image.png)
            static_emblem = self.renderer.render_static_emblem(w, h)
            static_emblem.save(os.path.join(theme_dir, "bgrt-fallback.png"), "PNG", optimize=True)
            static_emblem.save(os.path.join(theme_dir, "header-image.png"), "PNG", optimize=True)

            # 2. Isolated spinner frames (throbber-0001.png to throbber-0030.png, tiny 60x60 - 100x100 PNGs)
            total_throbber = min(30, max(1, total_frames))
            for t_idx in range(1, total_throbber + 1):
                spin_img = self.renderer.render_isolated_spinner_frame(t_idx - 1, total_frames=total_throbber)
                if spin_img is None:
                    spin_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

                throbber_file = os.path.join(theme_dir, f"throbber-{t_idx:04d}.png")
                anim_file = os.path.join(theme_dir, f"animation-{t_idx:04d}.png")
                spin_img.save(throbber_file, "PNG", optimize=True)
                spin_img.save(anim_file, "PNG", optimize=True)

                if progress_callback:
                    progress_callback(t_idx, total_throbber, f"Rendering smooth throbber {t_idx}/{total_throbber}...")

            # Save preview.png
            preview_comp = self.renderer.render_frame(preview_frame_idx, w, h)
            preview_path = os.path.join(theme_dir, "preview.png")
            preview_comp.resize((480, 270), Image.Resampling.LANCZOS).save(preview_path, "PNG")

        # 3. Create fallback UI assets (bullet, entry, lock)
        self._generate_auxiliary_assets(theme_dir)

        # 4. Generate .plymouth descriptor
        plymouth_file = os.path.join(theme_dir, f"{theme_name}.plymouth")
        self._write_plymouth_config(plymouth_file, theme_name, theme_dir, effective_module)

        # 5. Generate .script file (used directly for script module or as universal fallback)
        script_file = os.path.join(theme_dir, f"{theme_name}.script")
        self._write_plymouth_script(script_file, total_frames, w, h, offset_x, offset_y)

        # 6. Save project metadata
        self.project.save_to_file(os.path.join(theme_dir, "project.json"))

        if progress_callback:
            progress_callback(total_frames, total_frames, "Theme generation complete!")

        return theme_dir

    def _generate_auxiliary_assets(self, theme_dir: str):
        """Generates standard helper assets like bullet.png and lock.png for LUKS passphrase prompts."""
        from PIL import ImageDraw

        bullet = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        d = ImageDraw.Draw(bullet)
        d.ellipse([3, 3, 13, 13], fill=(255, 255, 255, 230))
        bullet.save(os.path.join(theme_dir, "bullet.png"))

        lock = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        d_lock = ImageDraw.Draw(lock)
        d_lock.rounded_rectangle([6, 14, 26, 30], radius=4, fill=(56, 189, 248, 255))
        d_lock.arc([10, 4, 22, 18], start=180, end=360, fill=(56, 189, 248, 255), width=3)
        d_lock.ellipse([14, 19, 18, 23], fill=(15, 23, 42, 255))
        lock.save(os.path.join(theme_dir, "lock.png"))

        entry = Image.new("RGBA", (280, 42), (0, 0, 0, 0))
        d_entry = ImageDraw.Draw(entry)
        d_entry.rounded_rectangle([1, 1, 278, 40], radius=8, fill=(15, 23, 42, 200), outline=(56, 189, 248, 180), width=2)
        entry.save(os.path.join(theme_dir, "entry.png"))

        caps = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        d_caps = ImageDraw.Draw(caps)
        d_caps.polygon([(12, 4), (5, 14), (9, 14), (9, 20), (15, 20), (15, 14), (19, 14)], fill=(255, 255, 255, 220))
        caps.save(os.path.join(theme_dir, "capslock.png"))

        kb = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        d_kb = ImageDraw.Draw(kb)
        d_kb.rounded_rectangle([2, 6, 22, 18], radius=3, outline=(255, 255, 255, 200), width=1)
        d_kb.rectangle([5, 9, 8, 11], fill=(255, 255, 255, 180))
        d_kb.rectangle([10, 9, 13, 11], fill=(255, 255, 255, 180))
        d_kb.rectangle([15, 9, 18, 11], fill=(255, 255, 255, 180))
        d_kb.rectangle([7, 13, 16, 15], fill=(255, 255, 255, 180))
        kb.save(os.path.join(theme_dir, "keyboard.png"))

        watermark = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        watermark.save(os.path.join(theme_dir, "watermark.png"))

    def _write_plymouth_config(self, filepath: str, theme_name: str, theme_dir: str, module_name: str = "script"):
        c1 = self.project.bg_color_1.replace("#", "0x")
        c2 = self.project.bg_color_2.replace("#", "0x")

        if module_name == "script":
            content = f"""[Plymouth Theme]
Name={self.project.display_name}
Description=MsmLogo high-performance boot animation for Linux
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/{theme_name}
ScriptFile=/usr/share/plymouth/themes/{theme_name}/{theme_name}.script
"""
        else:
            content = f"""[Plymouth Theme]
Name={self.project.display_name}
Description=MsmLogo native stock boot theme for Linux
ModuleName=two-step

[two-step]
ImageDir=/usr/share/plymouth/themes/{theme_name}
Font=DejaVu Sans 12
TitleFont=DejaVu Sans Bold 20
HorizontalAlignment=.5
VerticalAlignment=.5
Transition=none
TransitionDuration=0.0
BackgroundStartColor={c1}
BackgroundEndColor={c2}
ProgressBarBackgroundColor=0x334155
ProgressBarForegroundColor=0x38bdf8
MessageBelowAnimation=true

[boot-up]
UseEndAnimation=false

[shutdown]
UseEndAnimation=false

[reboot]
UseEndAnimation=false

[updates]
SuppressMessages=true
ProgressBarShowPercentComplete=true
UseProgressBar=true
Title=Installing Updates...
SubTitle=Do not turn off your computer
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def _write_plymouth_script(self, filepath: str, total_frames: int, width: int, height: int, offset_x: int = 0, offset_y: int = 0):
        script_content = f"""# Plymouth Script generated by MsmLogo
screen_w = Window.GetWidth();
screen_h = Window.GetHeight();

design_w = {width};
design_h = {height};

# Resolution scaling factor: ensures logo & text size always match design proportions on any monitor/resolution
scale = screen_h / design_h;
need_scale = 0;
if (scale < 0.98) need_scale = 1;
if (scale > 1.02) need_scale = 1;

# 1. Static Background (Rendered once, zero CPU overhead)
bg_image = Image("background.png");
if (bg_image) {{
    resized_bg = bg_image.Scale(screen_w, screen_h);
    bg_sprite = Sprite(resized_bg);
    bg_sprite.SetZ(-100);
    bg_sprite.SetX(0);
    bg_sprite.SetY(0);
}}

# 2. Optimized Cropped Animation Frames
frame_count = {total_frames};
anim_frames = [];
for (i = 1; i <= frame_count; i++) {{
    if (i < 10) num = "000" + i;
    else if (i < 100) num = "00" + i;
    else if (i < 1000) num = "0" + i;
    else num = "" + i;
    raw_img = Image("animation-" + num + ".png");
    if (raw_img) {{
        if (need_scale) {{
            target_w = Math.Int(raw_img.GetWidth() * scale);
            target_h = Math.Int(raw_img.GetHeight() * scale);
            anim_frames[i] = raw_img.Scale(target_w, target_h);
        }} else {{
            anim_frames[i] = raw_img;
        }}
    }}
}}

anim_sprite = Sprite();
anim_sprite.SetZ(10);

# Position sprite centered with exact resolution-scaled layout offset
first_frame = anim_frames[1];
if (first_frame) {{
    frame_w = first_frame.GetWidth();
    frame_h = first_frame.GetHeight();
    anim_x = (screen_w / 2) - (frame_w / 2) + Math.Int({offset_x} * scale);
    anim_y = (screen_h / 2) - (frame_h / 2) + Math.Int({offset_y} * scale);
    anim_sprite.SetPosition(anim_x, anim_y, 10);
}}

curr_frame = 0;
fun refresh_callback () {{
    curr_frame = (curr_frame + 1) % frame_count;
    idx = curr_frame + 1;
    frame_img = anim_frames[idx];
    if (frame_img) {{
        anim_sprite.SetImage(frame_img);
    }}
}}

fun quit_callback () {{
    anim_sprite.SetOpacity(0);
    if (bg_sprite) bg_sprite.SetOpacity(0);
}}

Plymouth.SetRefreshFunction(refresh_callback);
Plymouth.SetQuitFunction(quit_callback);
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(script_content)

