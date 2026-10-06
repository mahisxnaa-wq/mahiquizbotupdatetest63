import io
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# ==========================================
# QUESTION IMAGE CARD GENERATOR (SEGMENTED DUAL FONT ENGINE)
# Guarantees 100% ZERO BOX/TOFU ERRORS for mixed Hindi + English in the same line!
# Exact match of Purple Card Design (Image 2) with Custom Background Watermark Logo
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


def _measure_segment_width(text: str, font_hi: ImageFont.FreeTypeFont, font_en: ImageFont.FreeTypeFont, draw: ImageDraw.Draw) -> int:
    segments = re.findall(r'[\u0900-\u097F]+|[^\u0900-\u097F]+', text)
    total_w = 0
    for seg in segments:
        is_hi = any('\u0900' <= c <= '\u097F' for c in seg)
        f = font_hi if is_hi else font_en
        bbox = draw.textbbox((0, 0), seg, font=f)
        total_w += bbox[2] - bbox[0]
    return total_w


def _draw_segment_line(draw: ImageDraw.Draw, x: int, y: int, text: str, font_hi: ImageFont.FreeTypeFont, font_en: ImageFont.FreeTypeFont, fill: tuple) -> int:
    segments = re.findall(r'[\u0900-\u097F]+|[^\u0900-\u097F]+', text)
    curr_x = x
    for seg in segments:
        is_hi = any('\u0900' <= c <= '\u097F' for c in seg)
        f = font_hi if is_hi else font_en
        draw.text((curr_x, y), seg, font=f, fill=fill)
        bbox = draw.textbbox((0, 0), seg, font=f)
        curr_x += bbox[2] - bbox[0]
    return curr_x


def _wrap_mixed_text(text: str, font_hi: ImageFont.FreeTypeFont, font_en: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list:
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        w = _measure_segment_width(test_line, font_hi, font_en, draw)
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
    Generates a Purple Question Card Image with Watermark Logo and Segmented Font Engine (ZERO BOX ERRORS).
    """
    font_hi_main = _load_hi_font(28)
    font_en_main = _load_en_font(28)
    font_hi_sub = _load_hi_font(22)
    font_en_sub = _load_en_font(22)
    font_hi_opt = _load_hi_font(24)
    font_en_opt = _load_en_font(24)
    font_en_badge = _load_en_font(34)
    font_en_marks = _load_en_font(20)
    font_en_letter = _load_en_font(30)
    font_en_footer = _load_en_font(18)

    opt_prefixes = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    # Measure dynamic text height
    tmp_img = Image.new("RGB", (CARD_WIDTH, 100))
    tmp_draw = ImageDraw.Draw(tmp_img)
    max_text_width = CARD_WIDTH - 120

    q_lines_raw = [l.strip() for l in question_text.strip().split("\n") if l.strip()]
    wrapped_q_lines = []
    for line in q_lines_raw:
        wrapped = _wrap_mixed_text(line, font_hi_main, font_en_main, max_text_width, tmp_draw)
        wrapped_q_lines.extend(wrapped)

    q_text_height = len(wrapped_q_lines) * 42

    num_opts = min(len(options), 10)
    opt_boxes_info = []
    total_opts_h = 0

    for idx in range(num_opts):
        opt_str = options[idx]
        wrapped_opt = _wrap_mixed_text(opt_str, font_hi_opt, font_en_opt, CARD_WIDTH - 200, tmp_draw)
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
            target_logo_size = int(total_height * 0.75)
            logo_resized = logo_raw.resize((target_logo_size, target_logo_size), Image.Resampling.LANCZOS)
            
            mask = Image.new("L", (target_logo_size, target_logo_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, target_logo_size, target_logo_size], fill=180)
            
            logo_resized.putalpha(mask)
            enhancer = ImageEnhance.Brightness(logo_resized)
            logo_blended = enhancer.enhance(0.7)
            
            logo_x = (CARD_WIDTH - target_logo_size) // 2
            logo_y = (total_height - target_logo_size) // 2
            
            base_img.paste(logo_blended, (logo_x, logo_y), logo_blended)
        except Exception as le:
            print(f"⚠️ Logo watermark error: {le}")

    # Create drawing layer
    card_layer = Image.new("RGBA", (CARD_WIDTH, total_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card_layer)

    # Outer border container
    draw.rounded_rectangle(
        [16, 16, CARD_WIDTH - 16, total_height - 16],
        radius=24, fill=CARD_BG + (215,), outline=BORDER_PURPLE + (255,), width=2
    )

    # --- Top Header ---
    # Left Ribbon Badge Q1
    badge_poly = [
        (40, 32),
        (140, 32),
        (165, 72),
        (140, 72),
        (40, 72)
    ]
    draw.polygon(badge_poly, fill=BADGE_PURPLE + (255,))
    draw.text((62, 36), f"Q{q_number}", font=font_en_badge, fill=TEXT_WHITE + (255,))

    # Right Marks Badge
    right_label = f"Marks: {marks_str}" if marks_str else f"Q {q_number}/{total_questions}"
    mbbox = draw.textbbox((0, 0), right_label, font=font_en_marks)
    mw = mbbox[2] - mbbox[0]
    draw.rounded_rectangle([CARD_WIDTH - 70 - mw, 36, CARD_WIDTH - 40, 72], radius=10, fill=(24, 18, 55, 230), outline=BORDER_PURPLE + (255,), width=1)
    draw.text((CARD_WIDTH - 55 - mw, 43), right_label, font=font_en_marks, fill=TEXT_WHITE + (255,))

    # --- Question Box ---
    draw.rounded_rectangle(
        [38, q_box_top, CARD_WIDTH - 38, q_box_bottom],
        radius=18, fill=(22, 15, 48, 220), outline=BORDER_PURPLE + (255,), width=2
    )

    y_cursor = q_box_top + 20
    for line_idx, line in enumerate(wrapped_q_lines):
        f_hi = font_hi_main if line_idx == 0 else font_hi_sub
        f_en = font_en_main if line_idx == 0 else font_en_sub
        color = TEXT_WHITE if line_idx == 0 else TEXT_MUTED
        _draw_segment_line(draw, 60, y_cursor, line, f_hi, f_en, color + (255,))
        y_cursor += 40

    # --- Option Cards ---
    y_cursor = opts_top

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
        lbbox = draw.textbbox((0, 0), letter, font=font_en_letter)
        lw = lbbox[2] - lbbox[0]
        lh = lbbox[3] - lbbox[1]
        draw.text((cx1 + (52 - lw) // 2, cy1 + (52 - lh) // 2 - 4), letter, font=font_en_letter, fill=TEXT_WHITE + (255,))

        # Render Option Text lines using Segmented Dual-Font engine
        ot_y = box_y1 + (box_h - len(wrapped_opt) * 34) // 2
        for ol in wrapped_opt:
            _draw_segment_line(draw, 130, ot_y, ol, font_hi_opt, font_en_opt, TEXT_WHITE + (255,))
            ot_y += 34

        if is_correct:
            draw.text((CARD_WIDTH - 90, box_y1 + 18), "✓", font=font_en_letter, fill=CORRECT_GREEN + (255,))

        y_cursor = box_y2 + 14

    # --- Footer ---
    footer_y = total_height - 42
    draw.line([(38, footer_y - 8), (CARD_WIDTH - 38, footer_y - 8)], fill=OPT_BOX_BORDER + (255,), width=1)
    footer_text = "MAHI QUIZ BOT  ▪  STUDY  ▪  STRATEGY  ▪  DISCIPLINE"
    fbbox = draw.textbbox((0, 0), footer_text, font=font_en_footer)
    fw = fbbox[2] - fbbox[0]
    draw.text(((CARD_WIDTH - fw) // 2, footer_y + 2), footer_text, font=font_en_footer, fill=TEXT_MUTED + (255,))

    # Composite layers
    final_img = Image.alpha_composite(base_img, card_layer).convert("RGB")

    buf = io.BytesIO()
    final_img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
