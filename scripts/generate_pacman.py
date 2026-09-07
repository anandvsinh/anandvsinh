import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIG
# ============================================================

DATA_FILE = Path("leetcode_data.json")
OUTPUT_DIR = Path("assets")
OUTPUT_FILE = OUTPUT_DIR / "leetcode-pacman.gif"

WIDTH = 1400
HEIGHT = 500

BG = (7, 10, 15)
PANEL = (12, 17, 25)
GRID_EMPTY = (20, 28, 38)

GREEN_1 = (25, 110, 55)
GREEN_2 = (30, 170, 70)
GREEN_3 = (45, 220, 90)

YELLOW = (255, 215, 0)
YELLOW_BRIGHT = (255, 235, 60)

WHITE = (240, 245, 250)
MUTED = (120, 135, 155)

BLUE = (40, 100, 220)
RED = (245, 70, 70)
PINK = (235, 80, 160)
CYAN = (50, 210, 230)


# ============================================================
# FONTS
# ============================================================

def load_font(size, bold=False):
    candidates = []

    if bold:
        candidates += [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/consolab.ttf",
        ]
    else:
        candidates += [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/consola.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass

    return ImageFont.load_default()


FONT_TITLE = load_font(42, True)
FONT_SUBTITLE = load_font(20, True)
FONT_NORMAL = load_font(17)
FONT_SMALL = load_font(14)
FONT_STATS = load_font(27, True)


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_FILE.exists():
    raise FileNotFoundError(
        "leetcode_data.json not found. "
        "Run fetch_leetcode.py first."
    )

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

username = data["username"]
year = int(data["year"])
streak = int(data["streak"])
active_days = int(data["total_active_days"])

raw_calendar = data["submission_calendar"]


# Convert Unix timestamps to date -> submissions
calendar = {}

for timestamp, count in raw_calendar.items():
    timestamp = int(timestamp)

    date = datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc
    ).date()

    calendar[date] = int(count)


# ============================================================
# CALENDAR GRID
# ============================================================

start_date = datetime(year, 1, 1, tzinfo=timezone.utc).date()
end_date = datetime(year, 12, 31, tzinfo=timezone.utc).date()

# Find Monday before/at Jan 1
grid_start = start_date - timedelta(
    days=start_date.weekday()
)

# Find Sunday after/at Dec 31
grid_end = end_date + timedelta(
    days=6 - end_date.weekday()
)

dates = []

current = grid_start

while current <= grid_end:
    dates.append(current)
    current += timedelta(days=1)


# 7 rows × number of weeks
weeks = math.ceil(len(dates) / 7)

# Grid positioning
GRID_X = 90
GRID_Y = 175

CELL = 16
GAP = 5
STEP = CELL + GAP


def cell_position(date):
    index = (date - grid_start).days

    week = index // 7
    weekday = index % 7

    x = GRID_X + week * STEP
    y = GRID_Y + weekday * STEP

    return x, y


# ============================================================
# FIND CURRENT STREAK DAYS
# ============================================================

active_dates = set(
    date for date, count in calendar.items()
    if count > 0
)

streak_dates = set()

cursor = end_date

while cursor in active_dates:
    streak_dates.add(cursor)
    cursor -= timedelta(days=1)


# ============================================================
# DRAW HELPERS
# ============================================================

def rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(
        xy,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width
    )


def draw_pacman(draw, cx, cy, frame):
    radius = 11

    # Mouth animation
    mouth = 18 + int(
        18 * abs(math.sin(frame * 0.8))
    )

    direction = 0

    start = direction + mouth
    end = direction + 360 - mouth

    draw.pieslice(
        [
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius
        ],
        start=start,
        end=end,
        fill=YELLOW
    )

    # Eye
    draw.ellipse(
        [
            cx + 2,
            cy - 7,
            cx + 5,
            cy - 4
        ],
        fill=(10, 10, 10)
    )


def draw_ghost(draw, cx, cy, color, frame):

    bounce = int(
        2 * math.sin(frame * 0.4)
    )

    cy += bounce

    r = 10

    # Head
    draw.ellipse(
        [
            cx - r,
            cy - r,
            cx + r,
            cy + r
        ],
        fill=color
    )

    # Body
    draw.rectangle(
        [
            cx - r,
            cy,
            cx + r,
            cy + 10
        ],
        fill=color
    )

    # Feet
    for offset in (-7, 0, 7):
        draw.polygon(
            [
                (cx + offset - 4, cy + 8),
                (cx + offset, cy + 3),
                (cx + offset + 4, cy + 8)
            ],
            fill=color
        )

    # Eyes
    for ex in (-4, 4):
        draw.ellipse(
            [
                cx + ex - 2,
                cy - 4,
                cx + ex + 2,
                cy
            ],
            fill=WHITE
        )


def draw_cell(draw, date, eaten=False):

    count = calendar.get(date, 0)

    x, y = cell_position(date)

    if count <= 0:
        fill = GRID_EMPTY

    elif count <= 2:
        fill = GREEN_1

    elif count <= 4:
        fill = GREEN_2

    else:
        fill = GREEN_3

    # Current streak gets a brighter border
    outline = None

    if date in streak_dates:
        outline = YELLOW_BRIGHT

    if eaten and count > 0:
        fill = PANEL

    rounded_rect(
        draw,
        [
            x,
            y,
            x + CELL,
            y + CELL
        ],
        3,
        fill,
        outline,
        1
    )


# ============================================================
# PAC-MAN ROUTE
# ============================================================

# Pac-Man scans the grid chronologically.
# We reverse every second row to create a continuous arcade path.

route = []

for weekday in range(7):

    row_dates = [
        d for d in dates
        if (d - grid_start).days % 7 == weekday
    ]

    if weekday % 2:
        row_dates.reverse()

    route.extend(row_dates)


# Only animate meaningful activity days.
targets = [
    d for d in route
    if calendar.get(d, 0) > 0
]


# ============================================================
# CREATE FRAMES
# ============================================================

frames = []

TOTAL_FRAMES = max(
    100,
    len(targets) * 7
)

for frame in range(TOTAL_FRAMES):

    img = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BG
    )

    draw = ImageDraw.Draw(img)

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    draw.text(
        (45, 28),
        "LEETCODE",
        font=FONT_TITLE,
        fill=YELLOW
    )

    draw.text(
        (48, 78),
        "EAT • SOLVE • REPEAT",
        font=FONT_SUBTITLE,
        fill=MUTED
    )

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    stats_x = 390

    draw.text(
        (stats_x, 35),
        f"STREAK  {streak} DAYS",
        font=FONT_STATS,
        fill=YELLOW_BRIGHT
    )

    draw.text(
        (stats_x, 78),
        f"ACTIVE DAYS  {active_days}",
        font=FONT_SUBTITLE,
        fill=GREEN_3
    )

    draw.text(
        (stats_x + 360, 35),
        username,
        font=FONT_SUBTITLE,
        fill=WHITE
    )

    draw.text(
        (stats_x + 360, 78),
        str(year),
        font=FONT_SUBTITLE,
        fill=MUTED
    )

    # --------------------------------------------------------
    # CALENDAR PANEL
    # --------------------------------------------------------

    rounded_rect(
        draw,
        (30, 120, WIDTH - 30, 430),
        10,
        PANEL,
        BLUE,
        1
    )

    # --------------------------------------------------------
    # MONTH LABELS
    # --------------------------------------------------------

    month_positions = {}

    for date in dates:

        if date.day == 1:

            x, y = cell_position(date)

            month_positions[date.month] = x

    for month, x in month_positions.items():

        month_name = datetime(
            year,
            month,
            1
        ).strftime("%b").upper()

        draw.text(
            (x, 137),
            month_name,
            font=FONT_SMALL,
            fill=MUTED
        )

    # --------------------------------------------------------
    # WEEKDAY LABELS
    # --------------------------------------------------------

    weekdays = [
        "MON",
        "TUE",
        "WED",
        "THU",
        "FRI",
        "SAT",
        "SUN"
    ]

    for i, name in enumerate(weekdays):

        y = GRID_Y + i * STEP

        draw.text(
            (40, y),
            name,
            font=FONT_SMALL,
            fill=MUTED
        )

    # --------------------------------------------------------
    # DETERMINE EATEN CELLS
    # --------------------------------------------------------

    target_index = min(
        len(targets),
        frame // 7
    )

    eaten = set(
        targets[:target_index]
    )

    # --------------------------------------------------------
    # DRAW CALENDAR
    # --------------------------------------------------------

    for date in dates:

        # Don't draw dates outside the year
        if date.year != year:
            continue

        draw_cell(
            draw,
            date,
            eaten=date in eaten
        )

    # --------------------------------------------------------
    # PAC-MAN POSITION
    # --------------------------------------------------------

    if targets:

        current_index = min(
            len(targets) - 1,
            frame // 7
        )

        current_date = targets[current_index]

        x, y = cell_position(current_date)

        cx = x + CELL // 2
        cy = y + CELL // 2

        draw_pacman(
            draw,
            cx,
            cy,
            frame
        )

    # --------------------------------------------------------
    # GHOSTS
    # --------------------------------------------------------

    ghost_positions = [
        (WIDTH - 180, 160, RED),
        (WIDTH - 130, 230, PINK),
        (WIDTH - 200, 300, CYAN)
    ]

    for gx, gy, color in ghost_positions:

        draw_ghost(
            draw,
            gx,
            gy,
            color,
            frame
        )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    draw.text(
        (45, 448),
        "PAC-MAN IS EATING YOUR LEETCODE ACTIVITY",
        font=FONT_SMALL,
        fill=WHITE
    )

    draw.text(
        (WIDTH - 300, 448),
        "UPDATED AUTOMATICALLY",
        font=FONT_SMALL,
        fill=GREEN_2
    )

    frames.append(img)


# ============================================================
# SAVE GIF
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

frames[0].save(
    OUTPUT_FILE,
    save_all=True,
    append_images=frames[1:],
    duration=90,
    loop=0,
    optimize=True
)

print()
print("========================================")
print("       PAC-MAN GENERATED")
print("========================================")
print(f"Output : {OUTPUT_FILE}")
print(f"Frames : {len(frames)}")
print(f"Streak : {streak} days")
print(f"Active : {active_days} days")
print("========================================")
