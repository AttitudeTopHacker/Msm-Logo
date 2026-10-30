"""High-performance frame rendering engine for Plymouth animations and boot screens."""

import math
import os
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageColor
from .models import ThemeProject, EffectConfig, TextItem


class BootRenderer:
    def __init__(self, project: ThemeProject):
        self.project = project
        self._cached_bgs: dict[str, Image.Image] = {}
        self._cached_logos: dict[str, Image.Image] = {}
        self._frame_cache: dict[str, Image.Image] = {}

    def invalidate_cache(self):
        self._cached_bgs.clear()
        self._cached_logos.clear()
        self._frame_cache.clear()

    def _hex_to_rgb(self, hex_code: str) -> Tuple[int, int, int]:
        try:
            return ImageColor.getrgb(hex_code)[:3]
        except Exception:
            return (255, 255, 255)

    def _hex_to_rgba(self, hex_code: str, alpha: int = 255) -> Tuple[int, int, int, int]:
        rgb = self._hex_to_rgb(hex_code)
        return (rgb[0], rgb[1], rgb[2], alpha)

    def get_background(self, width: int, height: int) -> Image.Image:
        bg_key = f"{self.project.bg_type}_{self.project.bg_color_1}_{self.project.bg_color_2}_{self.project.bg_image_path}_{width}_{height}"
        if bg_key in self._cached_bgs:
            return self._cached_bgs[bg_key].copy()

        c1 = self._hex_to_rgb(self.project.bg_color_1)
        c2 = self._hex_to_rgb(self.project.bg_color_2)

        if self.project.bg_type == "solid":
            bg = Image.new("RGBA", (width, height), (c1[0], c1[1], c1[2], 255))

        elif self.project.bg_type == "image" and self.project.bg_image_path and os.path.exists(self.project.bg_image_path):
            try:
                raw_bg = Image.open(self.project.bg_image_path).convert("RGBA")
                bg = raw_bg.resize((width, height), Image.Resampling.LANCZOS)
            except Exception:
                bg = Image.new("RGBA", (width, height), (c1[0], c1[1], c1[2], 255))

        elif self.project.bg_type == "gradient_linear":
            # Smooth vertical gradient using fast interpolated strip
            steps = min(height, 256)
            buf = bytearray(steps * 4)
            idx = 0
            for y in range(steps):
                ratio = y / max(1, steps - 1)
                buf[idx] = int(c1[0] + (c2[0] - c1[0]) * ratio)
                buf[idx + 1] = int(c1[1] + (c2[1] - c1[1]) * ratio)
                buf[idx + 2] = int(c1[2] + (c2[2] - c1[2]) * ratio)
                buf[idx + 3] = 255
                idx += 4
            strip = Image.frombytes("RGBA", (1, steps), bytes(buf))
            bg = strip.resize((width, height), Image.Resampling.BILINEAR)

        else:  # default "gradient_radial" / vignette
            # Draw radial gradient with downscaled buffer and precomputed LUT for ultra-fast generation
            tw, th = 160, 90
            tcx, tcy = tw / 2.0, th / 2.0
            t_max_r = math.sqrt(tcx * tcx + tcy * tcy)
            scale_255 = 255.0 / t_max_r

            lut = [
                bytes((
                    int(c1[0] + (c2[0] - c1[0]) * ((i / 255.0) ** 2)),
                    int(c1[1] + (c2[1] - c1[1]) * ((i / 255.0) ** 2)),
                    int(c1[2] + (c2[2] - c1[2]) * ((i / 255.0) ** 2)),
                    255
                ))
                for i in range(256)
            ]

            buf = bytearray(tw * th * 4)
            idx = 0
            for y in range(th):
                dy2 = (y - tcy) ** 2
                for x in range(tw):
                    dist = math.sqrt((x - tcx) ** 2 + dy2)
                    lut_idx = min(255, int(dist * scale_255))
                    buf[idx:idx + 4] = lut[lut_idx]
                    idx += 4

            thumb = Image.frombytes("RGBA", (tw, th), bytes(buf))
            bg = thumb.resize((width, height), Image.Resampling.BILINEAR)

        self._cached_bgs[bg_key] = bg
        return bg.copy()

    def get_raw_logo(self, target_max_dim: int) -> Image.Image:
        logo_path = self.project.logo_path
        cache_key = f"{logo_path}_{target_max_dim}"
        if cache_key in self._cached_logos:
            return self._cached_logos[cache_key].copy()

        if logo_path and os.path.exists(logo_path):
            try:
                if logo_path.lower().endswith(".svg"):
                    raw = self._render_svg(logo_path, target_max_dim)
                else:
                    raw = Image.open(logo_path).convert("RGBA")
                    w, h = raw.size
                    scale = target_max_dim / max(w, h)
                    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                    raw = raw.resize((nw, nh), Image.Resampling.LANCZOS)

                self._cached_logos[cache_key] = raw
                return raw.copy()
            except Exception as e:
                print(f"Error loading logo {logo_path}: {e}")

        # Fallback default emblem
        emblem = self._create_default_emblem(target_max_dim)
        self._cached_logos[cache_key] = emblem
        return emblem.copy()

    def _render_svg(self, svg_path: str, target_max_dim: int) -> Image.Image:
        # Use PyQt6.QtSvg to render SVG perfectly onto a high-res QImage and convert to PIL Image
        try:
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtGui import QPainter, QImage
            from PyQt6.QtCore import QSize, Qt
            
            renderer = QSvgRenderer(svg_path)
            default_size = renderer.defaultSize()
            dw = default_size.width() if default_size.width() > 0 else target_max_dim
            dh = default_size.height() if default_size.height() > 0 else target_max_dim
            scale = target_max_dim / max(dw, dh)
            nw, nh = max(1, int(dw * scale)), max(1, int(dh * scale))
            
            qimg = QImage(nw, nh, QImage.Format.Format_ARGB32_Premultiplied)
            qimg.fill(Qt.GlobalColor.transparent)
            painter = QPainter(qimg)
            renderer.render(painter)
            painter.end()
            
            # Convert QImage to PIL
            qimg = qimg.convertToFormat(QImage.Format.Format_RGBA8888)
            ptr = qimg.bits()
            ptr.setsize(nh * nw * 4)
            img = Image.frombuffer("RGBA", (nw, nh), bytes(ptr), "raw", "RGBA", 0, 1)
            return img
        except Exception as e:
            print("QtSvg render failed, fallback:", e)
            return self._create_default_emblem(target_max_dim)

    def _create_default_emblem(self, size: int) -> Image.Image:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pad = int(size * 0.1)
        w = int(size * 0.08)
        # Power ring
        d.arc([pad, pad, size - pad, size - pad], start=135, end=405, fill=(56, 189, 248, 255), width=w)
        d.line([size // 2, pad // 2, size // 2, size // 2], fill=(56, 189, 248, 255), width=w)
        return img

    def _apply_shimmer(self, logo: Image.Image, progress: float, config: EffectConfig) -> Image.Image:
        """Applies a smooth sweeping metallic/neon light reflection across the logo."""
        if not config.shimmer_enabled or config.shimmer_intensity <= 0.01:
            return logo

        w, h = logo.size
        # Get alpha mask of the logo
        alpha = logo.split()[3]
        if not alpha.getbbox():
            return logo

        # Compute diagonal shimmer sweep position
        # Sweep moves from -w to 2*w
        angle_rad = math.radians(config.shimmer_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        sweep_len = w + h
        pos = (progress * (sweep_len * 1.5)) - (sweep_len * 0.25)

        # Create shimmer beam mask
        shimmer_mask = Image.new("L", (w, h), 0)
        sh_draw = ImageDraw.Draw(shimmer_mask)
        beam_w = max(10, int(sweep_len * config.shimmer_width))

        # We draw a series of parallel lines with Gaussian-like falloff
        half_w = beam_w // 2
        for offset in range(-half_w, half_w + 1):
            dist_ratio = abs(offset) / max(1, half_w)
            val = int(255 * (1.0 - (dist_ratio * dist_ratio)) * config.shimmer_intensity)
            if val <= 0:
                continue
            
            # Line in rotated coordinates: x * cos + y * sin = pos + offset
            # Intercepts:
            curr_pos = pos + offset
            # Draw line across bounding box
            if abs(sin_a) > 0.001:
                y0 = (curr_pos - 0 * cos_a) / sin_a
                y1 = (curr_pos - w * cos_a) / sin_a
                sh_draw.line([(0, y0), (w, y1)], fill=val, width=2)
            else:
                x = curr_pos / cos_a
                sh_draw.line([(x, 0), (x, h)], fill=val, width=2)

        # Multiply shimmer mask with logo alpha so shimmer only appears on logo surface
        effective_mask = ImageChops.multiply(shimmer_mask, alpha)

        # Create colored shimmer layer
        shimmer_rgb = self._hex_to_rgb(config.shimmer_color)
        shimmer_layer = Image.new("RGBA", (w, h), (shimmer_rgb[0], shimmer_rgb[1], shimmer_rgb[2], 255))
        shimmer_layer.putalpha(effective_mask)

        # Additive blend onto logo
        result = logo.copy()
        result.alpha_composite(shimmer_layer)
        return result

    def _apply_glow(self, logo: Image.Image, progress: float, config: EffectConfig, scale: float = 1.0) -> Image.Image:
        """Creates a breathing radiant glow behind the logo."""
        if not config.glow_pulse_enabled:
            return logo

        w, h = logo.size
        glow_rgb = self._hex_to_rgb(config.glow_color)
        radius = max(2, int(config.glow_radius * scale))

        # Breathing pulse oscillation
        pulse = 0.5 * (1.0 + math.sin(2.0 * math.pi * progress - math.pi / 2.0))
        intensity = config.glow_min_intensity + (config.glow_max_intensity - config.glow_min_intensity) * pulse

        # Create glow mask from alpha
        alpha = logo.split()[3]
        glow_mask = alpha.filter(ImageFilter.GaussianBlur(radius))
        
        # Scale alpha by intensity using fast native C 256-value LUT
        lut = [min(255, max(0, int(i * intensity))) for i in range(256)]
        glow_mask = glow_mask.point(lut)

        # Pad canvas so glow doesn't get clipped
        pad = radius * 2
        comp = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        glow_img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (glow_rgb[0], glow_rgb[1], glow_rgb[2], 0))
        
        glow_pad_mask = Image.new("L", (w + pad * 2, h + pad * 2), 0)
        glow_pad_mask.paste(glow_mask, (pad, pad))
        glow_img.putalpha(glow_pad_mask)

        comp.paste(glow_img, (0, 0), glow_img)
        comp.paste(logo, (pad, pad), logo)
        return comp

    def _draw_spinner(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, progress: float, config: EffectConfig, scale: float = 1.0):
        """Draws a smooth circular Linux boot throbber/spinner."""
        if not config.spinner_enabled or config.spinner_type == "none":
            return

        size = max(16, int(config.spinner_size * scale))
        half_s = size // 2
        bbox = [cx - half_s, cy - half_s, cx + half_s, cy + half_s]
        rot = (progress * 360.0 * config.spinner_speed_mult) % 360.0
        c1 = self._hex_to_rgba(config.spinner_color)
        c2 = self._hex_to_rgba(config.spinner_secondary_color)
        stroke = max(2, size // 10)

        st = config.spinner_type

        if st == "arc":
            # Elegant single spinning arc with trailing fade
            draw.arc(bbox, start=rot, end=rot + 270, fill=c1, width=stroke)

        elif st == "ring":
            # Circular ring with highlight dot
            draw.ellipse(bbox, outline=(c1[0], c1[1], c1[2], 60), width=stroke)
            draw.arc(bbox, start=rot, end=rot + 90, fill=c1, width=stroke + 1)

        elif st == "dual_ring":
            # Inner and outer counter-rotating rings
            draw.arc(bbox, start=rot, end=rot + 220, fill=c1, width=stroke)
            inner_pad = stroke * 2
            inner_bbox = [bbox[0] + inner_pad, bbox[1] + inner_pad, bbox[2] - inner_pad, bbox[3] - inner_pad]
            draw.arc(inner_bbox, start=360.0 - (rot * 1.5) % 360.0, end=360.0 - (rot * 1.5) % 360.0 + 180, fill=c2, width=max(2, stroke - 1))

        elif st == "dots":
            # 8 orbital dots with fading alpha
            num_dots = 8
            r = half_s - stroke
            for i in range(num_dots):
                ang_deg = rot + (i * (360.0 / num_dots))
                ang_rad = math.radians(ang_deg)
                dot_x = cx + r * math.cos(ang_rad)
                dot_y = cy + r * math.sin(ang_rad)
                dot_alpha = int(40 + (215 * (i / num_dots)))
                dot_r = max(2, stroke // 2 + (i // 3))
                draw.ellipse([dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r], fill=(c1[0], c1[1], c1[2], dot_alpha))

    def _render_text(self, canvas: Image.Image, cx: int, cy: int, text_item: TextItem, progress: float, scale: float = 1.0):
        """Renders styled text with optional font loading, drop shadow, and glow."""
        if not text_item.text.strip():
            return

        tx = cx + int(text_item.offset_x * scale)
        ty = cy + int(text_item.offset_y * scale)

        font_size = max(8, int(text_item.font_size * scale))
        
        # Try loading font or fallback
        font = None
        font_candidates = [
            f"/usr/share/fonts/truetype/dejavu/{text_item.font_family}-Bold.ttf" if text_item.is_bold else f"/usr/share/fonts/truetype/dejavu/{text_item.font_family}.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if text_item.is_bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if text_item.is_bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        for candidate in font_candidates:
            if os.path.exists(candidate):
                try:
                    font = ImageFont.truetype(candidate, font_size)
                    break
                except Exception:
                    continue
        if font is None:
            font = ImageFont.load_default()

        # Measure text
        draw = ImageDraw.Draw(canvas)
        bbox = draw.textbbox((0, 0), text_item.text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        x = tx - tw // 2
        y = ty - th // 2

        # Optional glow / drop shadow
        if text_item.glow_enabled:
            glow_rgb = self._hex_to_rgb(text_item.glow_color)
            # Create text mask for shadow
            blur_r = max(1, int(6 * scale))
            pad = max(8, int(20 * scale))
            text_mask = Image.new("L", (int(tw + pad * 2), int(th + pad * 2)), 0)
            t_draw = ImageDraw.Draw(text_mask)
            t_draw.text((pad, pad), text_item.text, font=font, fill=255)
            
            glow_blur = text_mask.filter(ImageFilter.GaussianBlur(blur_r))
            glow_layer = Image.new("RGBA", (int(tw + pad * 2), int(th + pad * 2)), (glow_rgb[0], glow_rgb[1], glow_rgb[2], 0))
            glow_layer.putalpha(glow_blur)
            canvas.alpha_composite(glow_layer, (int(x - pad), int(y - pad)))

        # Main text color
        text_rgb = self._hex_to_rgb(text_item.color)
        draw.text((int(x), int(y)), text_item.text, font=font, fill=(text_rgb[0], text_rgb[1], text_rgb[2], 255))

    def render_frame(self, frame_index: int, render_width: Optional[int] = None, render_height: Optional[int] = None) -> Image.Image:
        """Renders a single frame at the given frame index."""
        w = render_width or self.project.width
        h = render_height or self.project.height
        cache_key = f"{frame_index}_{w}_{h}"
        if cache_key in self._frame_cache:
            return self._frame_cache[cache_key].copy()

        total_f = max(1, self.project.total_frames)
        progress = (frame_index % total_f) / float(total_f)
        scale = h / float(self.project.height) if self.project.height > 0 else 1.0

        # 1. Background
        frame = self.get_background(w, h)

        # 2. Logo scaling & effects
        target_logo_dim = int(h * self.project.logo_scale)
        logo = self.get_raw_logo(target_logo_dim)

        # Zoom / Breathe effect
        cfg = self.project.effects
        if cfg.zoom_effect == "breathe":
            scale_mod = 1.0 + cfg.zoom_intensity * math.sin(2.0 * math.pi * progress)
            lw, lh = logo.size
            nw, nh = max(1, int(lw * scale_mod)), max(1, int(lh * scale_mod))
            logo = logo.resize((nw, nh), Image.Resampling.BILINEAR)
        elif cfg.zoom_effect == "zoom_in":
            scale_mod = 1.0 + cfg.zoom_intensity * progress
            lw, lh = logo.size
            nw, nh = max(1, int(lw * scale_mod)), max(1, int(lh * scale_mod))
            logo = logo.resize((nw, nh), Image.Resampling.BILINEAR)

        # Shimmer effect
        logo = self._apply_shimmer(logo, progress, cfg)

        # Pulse Glow effect
        logo_glow_comp = self._apply_glow(logo, progress, cfg, scale)

        # Position logo center
        cx = (w // 2) + int(self.project.logo_offset_x * scale)
        cy = (h // 2) + int(self.project.logo_offset_y * scale)

        lw, lh = logo_glow_comp.size
        lx = cx - lw // 2
        ly = cy - lh // 2

        # Paste logo with glow
        frame.alpha_composite(logo_glow_comp, (lx, ly))

        # 3. Texts
        for text_item in self.project.texts:
            self._render_text(frame, cx, cy, text_item, progress, scale)

        # 4. Spinner / Throbber
        draw = ImageDraw.Draw(frame)
        spinner_cx = cx + int(cfg.spinner_offset_x * scale)
        spinner_cy = cy + int(cfg.spinner_offset_y * scale)
        self._draw_spinner(draw, spinner_cx, spinner_cy, progress, cfg, scale)

        # 5. Global Fade In / Out
        if cfg.fade_in or cfg.fade_out:
            fade_ratio = max(0.01, cfg.fade_duration_ratio)
            alpha_mult = 1.0
            if cfg.fade_in and progress < fade_ratio:
                alpha_mult = progress / fade_ratio
            elif cfg.fade_out and progress > (1.0 - fade_ratio):
                alpha_mult = (1.0 - progress) / fade_ratio

            if alpha_mult < 0.999:
                black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
                frame = Image.blend(black, frame, max(0.0, min(1.0, alpha_mult)))

        self._frame_cache[cache_key] = frame
        return frame.copy()

    def render_foreground_frame(self, frame_index: int, render_width: Optional[int] = None, render_height: Optional[int] = None) -> Image.Image:
        """Renders only the foreground animated elements (logo, shimmer, glow, text, spinner) on a transparent canvas."""
        w = render_width or self.project.width
        h = render_height or self.project.height
        scale = h / float(self.project.height) if self.project.height > 0 else 1.0
        total_f = max(1, self.project.total_frames)
        progress = (frame_index % total_f) / float(total_f)

        frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        target_logo_dim = int(h * self.project.logo_scale)
        logo = self.get_raw_logo(target_logo_dim)

        cfg = self.project.effects
        if cfg.zoom_effect == "breathe":
            scale_mod = 1.0 + cfg.zoom_intensity * math.sin(2.0 * math.pi * progress)
            lw, lh = logo.size
            nw, nh = max(1, int(lw * scale_mod)), max(1, int(lh * scale_mod))
            logo = logo.resize((nw, nh), Image.Resampling.BILINEAR)
        elif cfg.zoom_effect == "zoom_in":
            scale_mod = 1.0 + cfg.zoom_intensity * progress
            lw, lh = logo.size
            nw, nh = max(1, int(lw * scale_mod)), max(1, int(lh * scale_mod))
            logo = logo.resize((nw, nh), Image.Resampling.BILINEAR)

        logo = self._apply_shimmer(logo, progress, cfg)
        logo_glow_comp = self._apply_glow(logo, progress, cfg, scale)

        cx = (w // 2) + int(self.project.logo_offset_x * scale)
        cy = (h // 2) + int(self.project.logo_offset_y * scale)

        lw, lh = logo_glow_comp.size
        lx = cx - lw // 2
        ly = cy - lh // 2

        frame.alpha_composite(logo_glow_comp, (lx, ly))

        for text_item in self.project.texts:
            self._render_text(frame, cx, cy, text_item, progress, scale)

        draw = ImageDraw.Draw(frame)
        spinner_cx = cx + int(cfg.spinner_offset_x * scale)
        spinner_cy = cy + int(cfg.spinner_offset_y * scale)
        self._draw_spinner(draw, spinner_cx, spinner_cy, progress, cfg, scale)

        return frame

    def get_unified_foreground_bbox(self, render_width: Optional[int] = None, render_height: Optional[int] = None) -> Tuple[int, int, int, int]:
        """Calculates a consistent unified bounding box that encloses the foreground across all animation stages."""
        w = render_width or self.project.width
        h = render_height or self.project.height
        total_f = max(1, self.project.total_frames)

        sample_indices = set([0, total_f // 4, total_f // 2, (3 * total_f) // 4, total_f - 1])
        min_x, min_y = w, h
        max_x, max_y = 0, 0

        for idx in sample_indices:
            fg = self.render_foreground_frame(idx, w, h)
            bbox = fg.getbbox()
            if bbox:
                min_x = min(min_x, bbox[0])
                min_y = min(min_y, bbox[1])
                max_x = max(max_x, bbox[2])
                max_y = max(max_y, bbox[3])

        if max_x <= min_x or max_y <= min_y:
            return (int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75))

        pad = 12
        min_x = max(0, min_x - pad)
        min_y = max(0, min_y - pad)
        max_x = min(w, max_x + pad)
        max_y = min(h, max_y + pad)

        return (min_x, min_y, max_x, max_y)

    def render_static_emblem(self, render_width: Optional[int] = None, render_height: Optional[int] = None) -> Image.Image:
        """Renders static emblem (logo + text) with transparent background and cropped to its bounding box."""
        w = render_width or self.project.width
        h = render_height or self.project.height
        scale = h / float(self.project.height) if self.project.height > 0 else 1.0
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

        target_logo_dim = int(h * self.project.logo_scale)
        logo = self.get_raw_logo(target_logo_dim)

        cx = (w // 2) + int(self.project.logo_offset_x * scale)
        cy = (h // 2) + int(self.project.logo_offset_y * scale)

        lw, lh = logo.size
        lx = cx - lw // 2
        ly = cy - lh // 2

        canvas.alpha_composite(logo, (lx, ly))

        for text_item in self.project.texts:
            self._render_text(canvas, cx, cy, text_item, 0.0, scale)

        bbox = canvas.getbbox()
        if bbox:
            pad = max(4, int(8 * scale))
            bx0 = max(0, bbox[0] - pad)
            by0 = max(0, bbox[1] - pad)
            bx1 = min(w, bbox[2] + pad)
            by1 = min(h, bbox[3] + pad)
            return canvas.crop((bx0, by0, bx1, by1))
        return canvas

    def render_isolated_spinner_frame(self, frame_index: int, total_frames: int = 30) -> Optional[Image.Image]:
        """Renders ONLY the spinner on an isolated transparent square. Perfect for Plymouth two-step throbber."""
        cfg = self.project.effects
        if not cfg.spinner_enabled or cfg.spinner_type == "none":
            return None

        size = max(24, cfg.spinner_size)
        pad = 4
        canvas_dim = size + pad * 2
        img = Image.new("RGBA", (canvas_dim, canvas_dim), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        progress = (frame_index % max(1, total_frames)) / float(max(1, total_frames))
        self._draw_spinner(draw, canvas_dim // 2, canvas_dim // 2, progress, cfg)
        return img

