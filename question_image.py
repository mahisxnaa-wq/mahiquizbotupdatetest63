import io
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# QUESTION IMAGE CARD GENERATOR
# Generates dark-themed Question Card Images
# for Telegram Quiz Bot (Image Card Mode)
# ==========================================

# Default Canvas Dimensions
CARD_WIDTH = 1200
CARD_MIN_HEIGHT = 500

# Color Palette
BG_COLOR = (15, 20, 28)
CARD_BG = (24, 32, 45)
ACCENT_RED = (220, 53, 69)
BORDER_COLOR = (45, 58, 78)
TEXT_WHITE = (240, 244, 248)
TEXT_MUTED = (160, 174, 192)
GOLD_ACCENT = (245, 158, 11)
OPT_BOX_BG = (30, 40, 56)
OPT_CIRCLE_BG = (45, 60, 85)
CORRECT_GREEN = (34, 197, 94)

# Font paths (tries multiple common locations)
FONT_CANDIDATES = [
    # Linux / Heroku / Docker (Noto Sans - supports Hindi)
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/google-noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    # Windows
    "C:\\Windows\\Fonts\\Nirmala.ttc",
    "C:\\Windows\\Fonts\\arial.ttf",
    # macOS
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _find_font_path() -> str:
    """Finds the first available font on the system."""
    for fp in FONT_CANDIDATES:
        if os.path.isfile(fp):
            return fp
    return ""


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Loads a TrueType font at the given size, falls back to default."""
    path = _find_font_path()
    if path:
        try:
            return ImageFont.truetype(path, size, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list:
    """Word-wraps text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
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
    correct_option_id: int = -1,
    show_answer: bool = False,
) -> io.BytesIO:
    """
    Generates a dark-themed Question Card Image.

    Args:
        question_text: The full question text (can be Hindi/English/mixed).
        options: List of option strings e.g. ["Option A text", "Option B text", ...].
        q_number: Current question number.
        total_questions: Total number of questions.
        quiz_name: Optional quiz name for header.
        correct_option_id: Index of correct option (0-based). -1 = don't show.
        show_answer: If True, highlights the correct option with green.

    Returns:
        BytesIO object containing the PNG image.
    """
    # Load fonts at various sizes
    font_badge = _load_font(34)
    font_q_main = _load_font(28)
    font_q_sub = _load_font(22)
    font_opt_letter = _load_font(30)
    font_opt_hi = _load_font(22)
    font_opt_en = _load_font(18)
    font_header_small = _load_font(18)

    opt_prefixes = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    # --- Phase 1: Calculate dynamic height ---
    # We need a temporary image to measure text sizes
    tmp_img = Image.new("RGB", (CARD_WIDTH, 100))
    tmp_draw = ImageDraw.Draw(tmp_img)

    max_text_width = CARD_WIDTH - 120  # padding on both sides

    # Split question into Hindi and English lines
    q_lines_raw = question_text.strip().split("\n")
    q_lines_raw = [l.strip() for l in q_lines_raw if l.strip()]

    # Try to detect bilingual: if there's a "/" separator or multiple lines
    # We'll render all lines as main question text
    wrapped_q_lines = []
    for line in q_lines_raw:
        wrapped = _wrap_text(line, font_q_main, max_text_width, tmp_draw)
        wrapped_q_lines.extend(wrapped)

    q_text_height = len(wrapped_q_lines) * 38  # ~38px per line

    # Options height calculation
    opt_box_h = 75
    opt_spacing = 14
    num_opts = min(len(options), 10)
    opts_total_height = num_opts * opt_box_h + (num_opts - 1) * opt_spacing

    # Total card height
    header_h = 70
    q_section_top = header_h + 20
    q_section_bottom = q_section_top + q_text_height + 30
    opts_section_top = q_section_bottom + 10
    opts_section_bottom = opts_section_top + opts_total_height + 20
    footer_h = 50

    total_height = opts_section_bottom + footer_h
    total_height = max(CARD_MIN_HEIGHT, total_height)

    # --- Phase 2: Draw actual image ---
    img = Image.new("RGB", (CARD_WIDTH, total_height), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Outer card with rounded rectangle
    draw.rounded_rectangle(
        [16, 16, CARD_WIDTH - 16, total_height - 16],
        radius=22, fill=CARD_BG, outline=(40, 50, 70), width=2
    )

    # --- Header Bar ---
    # Red badge with Q number
    badge_w = 40 + len(f"Q.{q_number}") * 20
    draw.rounded_rectangle([36, 32, 36 + badge_w, 82], radius=14, fill=ACCENT_RED)
    draw.text((52, 38), f"Q.{q_number}", font=font_badge, fill=(255, 255, 255))

    # Quiz name / counter on the right
    header_right_text = f"{q_number} / {total_questions}"
    if quiz_name:
        header_right_text = f"{quiz_name}  •  {header_right_text}"
    bbox_hr = draw.textbbox((0, 0), header_right_text, font=font_header_small)
    hr_w = bbox_hr[2] - bbox_hr[0]
    draw.text((CARD_WIDTH - 50 - hr_w, 45), header_right_text, font=font_header_small, fill=TEXT_MUTED)

    # Divider line
    draw.line([(36, header_h + 12), (CARD_WIDTH - 36, header_h + 12)], fill=BORDER_COLOR, width=2)

    # --- Question Text ---
    y_cursor = q_section_top + 10
    for line in wrapped_q_lines:
        draw.text((55, y_cursor), line, font=font_q_main, fill=TEXT_WHITE)
        y_cursor += 38

    # --- Options ---
    y_cursor = opts_section_top
    for idx in range(num_opts):
        opt_text = options[idx] if idx < len(options) else ""
        letter = opt_prefixes[idx] if idx < len(opt_prefixes) else str(idx + 1)

        box_y1 = y_cursor
        box_y2 = box_y1 + opt_box_h

        # Determine if this option should be highlighted (correct answer)
        is_correct = show_answer and idx == correct_option_id
        box_outline = CORRECT_GREEN if is_correct else BORDER_COLOR
        box_fill = (25, 50, 35) if is_correct else OPT_BOX_BG

        # Option card background
        draw.rounded_rectangle(
            [40, box_y1, CARD_WIDTH - 40, box_y2],
            radius=16, fill=box_fill, outline=box_outline, width=2
        )

        # Letter circle badge
        circle_fill = CORRECT_GREEN if is_correct else OPT_CIRCLE_BG
        cx1, cy1 = 58, box_y1 + 12
        cx2, cy2 = cx1 + 50, cy1 + 50
        draw.ellipse([cx1, cy1, cx2, cy2], fill=circle_fill)

        # Center letter in circle
        lbbox = draw.textbbox((0, 0), letter, font=font_opt_letter)
        lw = lbbox[2] - lbbox[0]
        lh = lbbox[3] - lbbox[1]
        draw.text((cx1 + (50 - lw) // 2, cy1 + (50 - lh) // 2 - 4), letter, font=font_opt_letter, fill=(255, 255, 255))

        # Option text - wrap if needed
        opt_max_w = CARD_WIDTH - 180
        opt_wrapped = _wrap_text(opt_text, font_opt_hi, opt_max_w, draw)
        if len(opt_wrapped) == 1:
            # Single line - center vertically
            draw.text((125, box_y1 + 24), opt_wrapped[0], font=font_opt_hi, fill=TEXT_WHITE)
        else:
            # Multi line
            oy = box_y1 + 12
            for ol in opt_wrapped[:3]:  # max 3 lines per option
                draw.text((125, oy), ol, font=font_opt_hi, fill=TEXT_WHITE)
                oy += 24

        # Tick mark for correct answer
        if is_correct:
            draw.text((CARD_WIDTH - 90, box_y1 + 22), "✓", font=font_opt_letter, fill=CORRECT_GREEN)

        y_cursor = box_y2 + opt_spacing

    # --- Footer ---
    footer_y = total_height - 45
    draw.line([(36, footer_y - 5), (CARD_WIDTH - 36, footer_y - 5)], fill=BORDER_COLOR, width=1)
    footer_text = "MAHI QUIZ BOT  •  STUDY  •  STRATEGY  •  DISCIPLINE"
    fbbox = draw.textbbox((0, 0), footer_text, font=font_header_small)
    fw = fbbox[2] - fbbox[0]
    draw.text(((CARD_WIDTH - fw) // 2, footer_y + 2), footer_text, font=font_header_small, fill=TEXT_MUTED)

    # Save to BytesIO
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
