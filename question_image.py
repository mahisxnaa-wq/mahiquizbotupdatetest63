import io
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

# ==========================================
# QUESTION IMAGE CARD GENERATOR (PREMIUM PRODUCTION EDITION)
# Exact match of visual reference with 10% Watermark Logo, 16:9 Landscape Layout,
# Unanswered 4 Equal Options, and Pristine Devanagari + English Typography.
# ==========================================

W, H = 1280, 720  # HD 16:9 Landscape Dimensions

# Theme Palette (Preserved dark navy / deep purple theme)
BG_DARK = (10, 8, 26)
CARD_BG = (17, 13, 38)
BORDER_PURPLE = (99, 102, 241)
BADGE_PURPLE = (124, 58, 237)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (195, 200, 225)
OPT_BG = (23, 17, 48)
OPT_BORDER = (67, 56, 202)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_HI_FONT = os.path.join(BASE_DIR, "NotoSansDevanagari-Regular.ttf")
LOCAL_EN_FONT = os.path.join(BASE_DIR, "NotoSans-Regular.ttf")
LOCAL_LOGO = os.path.join(BASE_DIR, "background_logo.jpg")

HI_FONT_URL = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf"
EN_FONT_URL = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"


def _ensure_font(local_path: str, url: str) -> str:
    if os.path.isfile(local_path) and os.path.getsize(local_path) > 1000:
        return local_path
    try:
        urllib.request.urlretrieve(url, local_path)
        if os.path.isfile(local_path):
            return local_path
    except Exception:
        pass
    return ""


def _load_hi_font(size: int) -> ImageFont.FreeTypeFont:
    # Try Windows Nirmala font first if available for native Devanagari shaping
    windows_nirmala = "C:\\Windows\\Fonts\\Nirmala.ttc"
    if os.path.isfile(windows_nirmala):
        try:
            return ImageFont.truetype(windows_nirmala, size, index=0)
        except Exception:
            pass
    fp = _ensure_font(LOCAL_HI_FONT, HI_FONT_URL)
    if fp:
        try:
            return ImageFont.truetype(fp, size, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


def _load_en_font(size: int) -> ImageFont.FreeTypeFont:
    windows_arial = "C:\\Windows\\Fonts\\arial.ttf"
    if os.path.isfile(windows_arial):
        try:
            return ImageFont.truetype(windows_arial, size)
        except Exception:
            pass
    fp = _ensure_font(LOCAL_EN_FONT, EN_FONT_URL)
    if fp:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            pass
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]
    for c in candidates:
        if os.path.isfile(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _clean_option_text(opt_str: str) -> str:
    """Strips any leading option prefix like A), B), C), D), 1., a) from option text."""
    clean = re.sub(r'^(?:[A-Da-d0-9][\.\)\:]\s*|[\(\[\{][A-Da-d0-9][\)\]\}]\s*)', '', str(opt_str)).strip()
    return clean if clean else str(opt_str).strip()


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
    Generates a Premium HD 16:9 Unanswered Question Card Image.
    Preserves all visual elements: Q1 badge, Marks box, Watermark behind text, 4 identical options, bottom footer.
    """
    font_en_badge = _load_en_font(32)
    font_en_marks = _load_en_font(20)
    font_hi_main = _load_hi_font(28)
    font_en_main = _load_en_font(21)
    font_en_letter = _load_en_font(28)
    font_hi_opt = _load_hi_font(24)
    font_en_opt = _load_en_font(20)
    font_en_footer = _load_en_font(17)

    opt_prefixes = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    # Separate Hindi question and English translation if separated by newline or slash
    q_lines_raw = [l.strip() for l in question_text.strip().split("\n") if l.strip()]
    q_hi = q_lines_raw[0] if len(q_lines_raw) > 0 else question_text
    q_en = q_lines_raw[1] if len(q_lines_raw) > 1 else ""

    # If no newline was present, check if separated by '/'
    if not q_en and "/" in q_hi:
        parts = q_hi.split("/", 1)
        q_hi = parts[0].strip()
        q_en = parts[1].strip()

    # Base Image Canvas
    base_img = Image.new("RGBA", (W, H), color=BG_DARK + (255,))

    # 10% Opacity Background Watermark Logo (BEHIND all text & cards)
    if os.path.isfile(LOCAL_LOGO):
        try:
            logo_raw = Image.open(LOCAL_LOGO).convert("RGBA")
            logo_size = 480
            logo_r = logo_raw.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Subtle low opacity watermark (approx 10%)
            alpha_channel = Image.new("L", (logo_size, logo_size), 26)
            logo_r.putalpha(alpha_channel)
            
            lx = (W - logo_size) // 2
            ly = (H - logo_size) // 2 - 20
            base_img.paste(logo_r, (lx, ly), logo_r)
        except Exception as le:
            print(f"⚠️ Logo watermark notice: {le}")

    # Drawing Overlay Layer
    card_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card_layer)

    # Outer Frame Border
    draw.rounded_rectangle([24, 24, W - 24, H - 24], radius=24, fill=CARD_BG + (215,), outline=BORDER_PURPLE + (255,), width=2)

    # Top Left Q1 Badge
    badge_poly = [(44, 40), (140, 40), (165, 80), (140, 80), (44, 80)]
    draw.polygon(badge_poly, fill=BADGE_PURPLE + (255,))
    draw.text((68, 44), f"Q{q_number}", font=font_en_badge, fill=TEXT_WHITE + (255,))

    # Top Right Marks Box
    right_label = f"Marks: {marks_str}" if marks_str else f"Q {q_number}/{total_questions}"
    mbbox = draw.textbbox((0, 0), right_label, font=font_en_marks)
    mw = mbbox[2] - mbbox[0]
    draw.rounded_rectangle([W - 64 - mw, 42, W - 44, 78], radius=12, fill=(24, 18, 55, 230), outline=BORDER_PURPLE + (255,), width=1)
    draw.text((W - 54 - mw, 49), right_label, font=font_en_marks, fill=TEXT_WHITE + (255,))

    # Question Container Box
    q_top = 100
    q_h = 130
    draw.rounded_rectangle([44, q_top, W - 44, q_top + q_h], radius=18, fill=(22, 15, 48, 220), outline=BORDER_PURPLE + (255,), width=2)

    # Hindi Question Text
    draw.text((68, q_top + 22), q_hi, font=font_hi_main, fill=TEXT_WHITE + (255,))
    
    # English Translation Text (below Hindi)
    if q_en:
        draw.text((68, q_top + 72), q_en, font=font_en_main, fill=TEXT_MUTED + (255,))

    # 4 Equal Unanswered Options (Identical height, background, border, circle accent)
    opt_top = q_top + q_h + 20
    box_h = 80
    spacing = 16
    num_opts = min(len(options), 4)

    for idx in range(num_opts):
        letter = opt_prefixes[idx] if idx < len(opt_prefixes) else str(idx + 1)
        opt_raw = options[idx]
        
        # Split option into Hindi and English if separated by '/'
        opt_clean = _clean_option_text(opt_raw)
        if "/" in opt_clean:
            oparts = opt_clean.split("/", 1)
            o_hi = oparts[0].strip()
            o_en = oparts[1].strip()
        else:
            o_hi = opt_clean
            o_en = ""

        y1 = opt_top + idx * (box_h + spacing)
        y2 = y1 + box_h
        
        # Option Box
        draw.rounded_rectangle([44, y1, W - 44, y2], radius=16, fill=OPT_BG + (210,), outline=OPT_BORDER + (255,), width=2)
        
        # Circle Badge
        cx1, cy1 = 64, y1 + 14
        cx2, cy2 = cx1 + 52, cy1 + 52
        draw.ellipse([cx1, cy1, cx2, cy2], fill=BADGE_PURPLE + (255,))
        
        lbbox = draw.textbbox((0, 0), letter, font=font_en_letter)
        lw, lh = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
        draw.text((cx1 + (52 - lw)//2, cy1 + (52 - lh)//2 - 3), letter, font=font_en_letter, fill=TEXT_WHITE + (255,))
        
        # Option Text Alignment: Hindi + English cleanly separated
        tx = 140
        ty = y1 + 24
        draw.text((tx, ty), o_hi, font=font_hi_opt, fill=TEXT_WHITE + (255,))
        
        if o_en:
            hibbox = draw.textbbox((0, 0), o_hi, font=font_hi_opt)
            hi_w = hibbox[2] - hibbox[0]
            
            slash_x = tx + hi_w + 14
            draw.text((slash_x, ty), '/', font=font_en_opt, fill=TEXT_MUTED + (255,))
            
            en_x = slash_x + 18
            draw.text((en_x, ty + 2), o_en, font=font_en_opt, fill=TEXT_MUTED + (255,))

    # Footer
    footer_y = H - 45
    draw.line([(44, footer_y - 10), (W - 44, footer_y - 10)], fill=OPT_BORDER + (255,), width=1)
    footer_text = "MAHI QUIZ BOT • STUDY • STRATEGY • DISCIPLINE"
    fbbox = draw.textbbox((0, 0), footer_text, font=font_en_footer)
    fw = fbbox[2] - fbbox[0]
    draw.text(((W - fw) // 2, footer_y + 2), footer_text, font=font_en_footer, fill=TEXT_MUTED + (255,))

    # Composite layers
    final_img = Image.alpha_composite(base_img, card_layer).convert("RGB")

    buf = io.BytesIO()
    final_img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
