import os
import sys
from PIL import Image, ImageDraw, ImageFont
import stories

# Design Tokens
CREAM = '#f3ecde'
CHARCOAL_1 = '#292722'
CHARCOAL_2 = '#211f1b'
GOLD = '#d9b568'
IVORY = '#f8f1e2'
INK = '#1c1a17'
MUTED = '#8a8172'

CANVAS_WIDTH = 1024
CANVAS_HEIGHT = 1024

def find_font_file(candidates):
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def load_font(name_key, size):
    font_paths = {
        'serif_bold': [
            '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
        ],
        'serif_regular': [
            '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
        ],
        'sans': [
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        ],
        'condensed': [
            '/usr/share/fonts/truetype/noto/NotoSansDisplayCondensed-Regular.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
        ]
    }
    candidates = font_paths.get(name_key, font_paths['sans'])
    path = find_font_file(candidates)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def region_colour(name):
    return stories.REGIONS.get(name, GOLD)

def gradient(draw, box, color1, color2, vertical=True):
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill=color1)

class Page:
    def __init__(self, width=CANVAS_WIDTH, height=CANVAS_HEIGHT):
        self.width = width
        self.height = height
        self.img = Image.new('RGB', (width, height), CREAM)
        self.draw = ImageDraw.Draw(self.img)
        self.boxes = []

    def card_surface(self, x0, y0, x1, y1, fill):
        self.draw.rectangle([x0, y0, x1, y1], fill=fill)

    def card_outline(self, x0, y0, x1, y1, outline, width=1):
        self.draw.rectangle([x0, y0, x1, y1], outline=outline, width=width)

    def text(self, xy, text_str, font, fill, max_width=None, spacing=4):
        x, y = xy
        if not text_str:
            return y
        
        words = text_str.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word]) if current_line else word
            if max_width is not None:
                bbox = self.draw.textbbox((0, 0), test_line, font=font)
                w = bbox[2] - bbox[0]
                if w > max_width and current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)
            else:
                current_line.append(word)
        if current_line:
            lines.append(' '.join(current_line))

        curr_y = y
        for line in lines:
            if not line:
                continue
            self.draw.text((x, curr_y), line, font=font, fill=fill)
            bbox = self.draw.textbbox((x, curr_y), line, font=font)
            self.boxes.append(bbox)
            line_height = bbox[3] - bbox[1]
            curr_y += line_height + spacing

        return curr_y

def self_check(page):
    for idx, (x0, y0, x1, y1) in enumerate(page.boxes):
        if x0 < 0 or y0 < 0 or x1 > page.width or y1 > page.height:
            raise ValueError(f"Text box {idx} out of bounds: ({x0}, {y0}, {x1}, {y1}) in canvas {page.width}x{page.height}")

    n = len(page.boxes)
    for i in range(n):
        ax0, ay0, ax1, ay1 = page.boxes[i]
        for j in range(i + 1, n):
            bx0, by0, bx1, by1 = page.boxes[j]
            intersects = (ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0)
            if intersects:
                a_in_b = (bx0 <= ax0 and ax1 <= bx1 and by0 <= ay0 and ay1 <= by1)
                b_in_a = (ax0 <= bx0 and bx1 <= ax1 and ay0 <= by0 and by1 <= ay1)
                if not (a_in_b or b_in_a):
                    raise ValueError(f"Text box collision between box {i} {page.boxes[i]} and box {j} {page.boxes[j]}")

import stories

def draw_masthead(page):
    title_text = stories.META['title']
    date_line = stories.META['date_line']
    edition = stories.META['edition']
    
    chosen_size = 40
    for sz in range(40, 9, -1):
        font = load_font('serif_bold', sz)
        dummy = Page()
        y_end = dummy.text((32, 6), title_text, font, INK, max_width=960)
        if len(dummy.boxes) <= 2 and y_end + 18 <= 88:
            chosen_size = sz
            break
            
    title_font = load_font('serif_bold', chosen_size)
    y_after_title = page.text((32, 6), title_text, title_font, INK, max_width=960)
    
    sans_font = load_font('sans', 11)
    sub_text = f"{date_line}   ·   {edition}"
    page.text((32, y_after_title + 2), sub_text, sans_font, MUTED, max_width=960)
    page.card_surface(32, 89, 992, 91, GOLD)

def draw_lead_card(page):
    import stories
    c = stories.CARDS[0]
    page.card_surface(32, 92, 992, 252, CHARCOAL_1)
    reg_col = region_colour(c.get('region', 'MIDDLE EAST'))
    page.draw.rectangle([32, 92, 36, 252], fill=reg_col)
    page.draw.ellipse([948, 150, 972, 195], fill=GOLD)
    page.draw.ellipse([952, 138, 968, 180], fill=GOLD)
    page.draw.ellipse([955, 160, 965, 188], fill=IVORY)
    f_meta = load_font('sans', 11)
    f_head = load_font('serif_bold', 30)
    f_deck = load_font('sans', 13)
    f_src = load_font('sans', 11)
    place_topic = f"{c['place'].upper()} • {c['topic'].upper()}"
    headline = c['headline']
    if page.draw.textbbox((0, 0), headline, font=f_head)[2] > 860:
        f_head = load_font('serif_bold', 24)
    y = 100
    y = page.text((48, y), place_topic, font=f_meta, fill=GOLD)
    y += 4
    y = page.text((48, y), headline, font=f_head, fill=CREAM)
    y += 4
    y = page.text((48, y), c['deck'], font=f_deck, fill=CREAM, max_width=760)
    y += 4
    y = page.text((48, y), f"{c['source'].upper()} • {c['tag'].upper()}", font=f_src, fill=GOLD)

def main():
    page = Page()
    draw_masthead(page)
    draw_lead_card(page)
    self_check(page)
    page.img.save('/home/hatch/workspace/makefun/entries/news-image-20261124-r1/entry.png')
    print("entry.png saved successfully.")

if __name__ == '__main__':
    main()
