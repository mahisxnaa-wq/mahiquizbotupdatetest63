import io
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# ==========================================
# QUESTION IMAGE CARD GENERATOR (PREMIUM WITH WATERMARK LOGO)
# Exact match of Purple Card Design (Image 2) with Custom Background Watermark Logo
# Guarantees ZERO tofu/box errors for Hindi + English
# ==========================================

CARD_WIDTH = 1200
CARD_MIN_HEIGHT = 650

# Color Palette (Matching User Reference Image 2)
BG_COLOR = (12, 8, 30)          # Dark purple background
CARD_BG = (18, 12, 42)          # Inner card background
BORDER_PURPLE = (99, 102, 241)  # Glowing purple outer border
BADGE_PURPLE = (124, 58, 237)   # Ribbon badge & option circles
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (216, 220, 240)
OPT_BOX_BG = (24, 16, 52)
OPT_BOX_BORDER = (67, 56, 202)
CORRECT_GREEN = (34, 197, 94)

# Paths
FONT_FILENAME = "NotoSansDevanagari-Regular.ttf"
LOGO_FILENAME = "background_logo.jpg"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_HI_FONT = os.path.join(BASE_DIR, FONT_FILENAME)
LOCAL_LOGO = os.path.join(BASE_DIR, LOGO_FILENAME)
HI_FONT_URL = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf"


def _ensure_hi_font() -> str:
    if os.path.isfile(LOCAL_HI_FONT) and os.path.getsize(LOCAL_HI_FONT) > 1000:
        return LOCAL_HI_FONT
    try:
        urllib.request.urlretrieve(HI_FONT_URL, LOCAL_HI_FONT)
        if os.path.isfile(LOCAL_HI_FONT):
            return LOCAL_HI_FONT
    except Exception:
        pass
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/noto/NotoSansDevanagari-Regular.ttf",
        "C:\\Windows\\Fonts\\Nirmala.ttc"
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return ""


def _load_hi_font(size: int) -> ImageFont.FreeTypeFont:
    fp = _ensure_hi_font()
    if fp:
        try:
            return ImageFont.truetype(fp, size, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


def _load_en_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf"
    ]
    for c in candidates:
        if os.path.isfile(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _has_devanagari(text: str) -> bool:
    return any('\u0900' <= char <= '\u097F' for char in text)


def _get_appropriate_font(text: str, size: int, font_hi_cache: dict, font_en_cache: dict) -> ImageFont.FreeTypeFont:
    if _has_devanagari(text):
        if size not in font_hi_cache:
            font_hi_cache[size] = _load_hi_font(size)
        return font_hi_cache[size]
    else:
        if size not in font_en_cache:
            font_en_cache[size] = _load_en_font(size)
        return font_en_cache[size]


def _wrap_text(text: str, size: int, max_width: int, draw: ImageDraw.Draw, font_hi_cache: dict, font_en_cache: dict) -> list:
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        font = _get_appropriate_font(test_line, size, font_hi_cache, font_en_cache)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines if lines else [text]


def generate_question_card(
    question_text: str,
    options: list,
    q_number: int = 1,
    total_questions: int = 1,
    quiz_name: str = "",
    marks_str: str = "2.00",
    correct_option_id: int = -1,
    show_answer: bool = False,
) -> io.BytesIO:
    """
    Generates a high-quality Purple Question Card Image with Watermark Logo (Reference Image 2).
    """
    font_hi_cache = {}
    font_en_cache = {}

    opt_prefixes = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    # Measure dynamic text height
    tmp_img = Image.new("RGB", (CARD_WIDTH, 100))
    tmp_draw = ImageDraw.Draw(tmp_img)
    max_text_width = CARD_WIDTH - 120

    q_lines_raw = [l.strip() for l in question_text.strip().split("\n") if l.strip()]
    wrapped_q_lines = []
    for line in q_lines_raw:
        wrapped = _wrap_text(line, 26, max_text_width, tmp_draw, font_hi_cache, font_en_cache)
        wrapped_q_lines.extend(wrapped)

    q_text_height = len(wrapped_q_lines) * 42

    num_opts = min(len(options), 10)
    opt_boxes_info = []
    total_opts_h = 0

    for idx in range(num_opts):
        opt_str = options[idx]
        wrapped_opt = _wrap_text(opt_str, 24, CARD_WIDTH - 200, tmp_draw, font_hi_cache, font_en_cache)
        box_h = max(70, 24 + len(wrapped_opt) * 34)
        opt_boxes_info.append((wrapped_opt, box_h))
        total_opts_h += box_h + 14

    header_h = 90
    q_box_top = header_h + 15
    q_box_h = max(110, q_text_height + 40)
    q_box_bottom = q_box_top + q_box_h

    opts_top = q_box_bottom + 18
    total_height = opts_top + total_opts_h + 60
    total_height = max(CARD_MIN_HEIGHT, total_height)

    # Base image creation
    base_img = Image.new("RGBA", (CARD_WIDTH, total_height), color=BG_COLOR + (255,))

    # Overlay Watermark Logo if present
    if os.path.isfile(LOCAL_LOGO):
        try:
            logo_raw = Image.open(LOCAL_LOGO).convert("RGBA")
            # Resize logo to fit centrally in background
            target_logo_size = int(total_height * 0.75)
            logo_resized = logo_raw.resize((target_logo_size, target_logo_size), Image.Resampling.LANCZOS)
            
            # Make circular mask for logo
            mask = Image.new("L", (target_logo_size, target_logo_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, target_logo_size, target_logo_size], fill=180)
            
            # Adjust opacity to ~35%
            logo_resized.putalpha(mask)
            enhancer = ImageEnhance.Brightness(logo_resized)
            logo_blended = enhancer.enhance(0.7)
            
            # Center logo position
            logo_x = (CARD_WIDTH - target_logo_size) // 2
            logo_y = (total_height - target_logo_size) // 2
            
            base_img.paste(logo_blended, (logo_x, logo_y), logo_blended)
        except Exception as le:
            print(f"⚠️ Logo watermark error: {le}")

    # Create drawing layer
    card_layer = Image.new("RGBA", (CARD_WIDTH, total_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card_layer)

    # Outer border container (semi-transparent card surface so watermark shines through)
    draw.rounded_rectangle(
        [16, 16, CARD_WIDTH - 16, total_height - 16],
        radius=24, fill=CARD_BG + (215,), outline=BORDER_PURPLE + (255,), width=2
    )

    # --- Top Header ---
    # Left Ribbon Badge Q1
    font_badge = _get_appropriate_font(f"Q{q_number}", 34, font_hi_cache, font_en_cache)
    badge_poly = [
        (40, 32),
        (140, 32),
        (165, 72),
        (140, 72),
        (40, 72)
    ]
    draw.polygon(badge_poly, fill=BADGE_PURPLE + (255,))
    draw.text((62, 36), f"Q{q_number}", font=font_badge, fill=TEXT_WHITE + (255,))

    # Right Marks Badge
    font_marks = _get_appropriate_font(f"Marks: {marks_str}", 20, font_hi_cache, font_en_cache)
    right_label = f"Marks: {marks_str}" if marks_str else f"Q {q_number}/{total_questions}"
    mbbox = draw.textbbox((0, 0), right_label, font=font_marks)
    mw = mbbox[2] - mbbox[0]
    draw.rounded_rectangle([CARD_WIDTH - 70 - mw, 36, CARD_WIDTH - 40, 72], radius=10, fill=(24, 18, 55, 230), outline=BORDER_PURPLE + (255,), width=1)
    draw.text((CARD_WIDTH - 55 - mw, 43), right_label, font=font_marks, fill=TEXT_WHITE + (255,))

    # --- Question Box ---
    draw.rounded_rectangle(
        [38, q_box_top, CARD_WIDTH - 38, q_box_bottom],
        radius=18, fill=(22, 15, 48, 220), outline=BORDER_PURPLE + (255,), width=2
    )

    y_cursor = q_box_top + 20
    for line_idx, line in enumerate(wrapped_q_lines):
        size = 28 if line_idx == 0 else 22
        font = _get_appropriate_font(line, size, font_hi_cache, font_en_cache)
        color = TEXT_WHITE if line_idx == 0 else TEXT_MUTED
        draw.text((60, y_cursor), line, font=font, fill=color + (255,))
        y_cursor += 40

    # --- Option Cards ---
    y_cursor = opts_top
    font_letter = _get_appropriate_font("A", 30, font_hi_cache, font_en_cache)

    for idx, (wrapped_opt, box_h) in enumerate(opt_boxes_info):
        letter = opt_prefixes[idx] if idx < len(opt_prefixes) else str(idx + 1)
        box_y1 = y_cursor
        box_y2 = box_y1 + box_h

        is_correct = show_answer and idx == correct_option_id
        box_fill = (25, 50, 35, 230) if is_correct else OPT_BOX_BG + (210,)
        box_outline = CORRECT_GREEN if is_correct else OPT_BOX_BORDER

        # Option Card Box
        draw.rounded_rectangle(
            [38, box_y1, CARD_WIDTH - 38, box_y2],
            radius=18, fill=box_fill, outline=box_outline + (255,), width=2
        )

        # Circle Badge
        cx1, cy1 = 56, box_y1 + (box_h - 52) // 2
        cx2, cy2 = cx1 + 52, cy1 + 52
        circle_fill = CORRECT_GREEN if is_correct else BADGE_PURPLE
        draw.ellipse([cx1, cy1, cx2, cy2], fill=circle_fill + (255,))

        # Center Letter
        lbbox = draw.textbbox((0, 0), letter, font=font_letter)
        lw = lbbox[2] - lbbox[0]
        lh = lbbox[3] - lbbox[1]
        draw.text((cx1 + (52 - lw) // 2, cy1 + (52 - lh) // 2 - 4), letter, font=font_letter, fill=TEXT_WHITE + (255,))

        # Render Option Text lines
        ot_y = box_y1 + (box_h - len(wrapped_opt) * 34) // 2
        for ol in wrapped_opt:
            font_opt = _get_appropriate_font(ol, 24, font_hi_cache, font_en_cache)
            draw.text((130, ot_y), ol, font=font_opt, fill=TEXT_WHITE + (255,))
            ot_y += 34

        if is_correct:
            draw.text((CARD_WIDTH - 90, box_y1 + 18), "✓", font=font_letter, fill=CORRECT_GREEN + (255,))

        y_cursor = box_y2 + 14

    # --- Footer ---
    footer_y = total_height - 42
    draw.line([(38, footer_y - 8), (CARD_WIDTH - 38, footer_y - 8)], fill=OPT_BOX_BORDER + (255,), width=1)
    footer_text = "MAHI QUIZ BOT  ▪  STUDY  ▪  STRATEGY  ▪  DISCIPLINE"
    font_footer = _get_appropriate_font(footer_text, 18, font_hi_cache, font_en_cache)
    fbbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    fw = fbbox[2] - fbbox[0]
    draw.text(((CARD_WIDTH - fw) // 2, footer_y + 2), footer_text, font=font_footer, fill=TEXT_MUTED + (255,))

    # Composite layers
    final_img = Image.alpha_composite(base_img, card_layer).convert("RGB")

    buf = io.BytesIO()
    final_img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
