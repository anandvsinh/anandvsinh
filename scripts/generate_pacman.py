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

GREEN_1 = (25, 105, 52)
GREEN_2 = (30, 165, 70)
GREEN_3 = (45, 220, 90)

YELLOW = (255, 215, 0)
YELLOW_BRIGHT = (255, 235, 60)

WHITE = (240, 245, 250)
MUTED = (115, 130, 150)

BLUE = (45, 100, 210)

RED = (245, 70, 70)
PINK = (235, 80, 160)
CYAN = (50, 210, 230)


# ============================================================
# FONTS
# ============================================================

def load_font(size, bold=False):

    candidates = []

    if bold:
        candidates = [
            "C:/Windows/Fonts/consolab.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass

    return ImageFont.load_default()


FONT_TITLE = load_font(42, True)
FONT_SUBTITLE = load_font(19, True)
FONT_NORMAL = load_font(16)
FONT_SMALL = load_font(13)
FONT_STATS = load_font(25, True)


# ============================================================
# LOAD LEETCODE DATA
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


calendar = {}

for timestamp, count in raw_calendar.items():

    timestamp = int(timestamp)

    date = datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc
    ).date()

    calendar[date] = int(count)


# ============================================================
# CALENDAR
# ============================================================

start_date = datetime(
    year,
    1,
    1,
    tzinfo=timezone.utc
).date()

end_date = datetime(
    year,
    12,
    31,
    tzinfo=timezone.utc
).date()


grid_start = start_date - timedelta(
    days=start_date.weekday()
)

grid_end = end_date + timedelta(
    days=6 - end_date.weekday()
)


dates = []

current = grid_start

while current <= grid_end:

    dates.append(current)

    current += timedelta(days=1)


CELL = 17
GAP = 5
STEP = CELL + GAP

GRID_X = 90
GRID_Y = 175


def cell_position(date):

    index = (date - grid_start).days

    week = index // 7
    weekday = index % 7

    x = GRID_X + week * STEP
    y = GRID_Y + weekday * STEP

    return x, y


# ============================================================
# CURRENT STREAK
# ============================================================

active_dates = {
    date
    for date, count in calendar.items()
    if count > 0
}


streak_dates = set()

cursor = end_date

while cursor in active_dates:

    streak_dates.add(cursor)

    cursor -= timedelta(days=1)


# ============================================================
# DRAW PAC-MAN
# ============================================================

def draw_pacman(
    draw,
    cx,
    cy,
    direction,
    frame
):

    radius = 11

    # Mouth animation
    mouth = 8 + int(
        22 * abs(math.sin(frame * 0.65))
    )

    direction_angles = {
        "right": 0,
        "down": 90,
        "left": 180,
        "up": 270,
    }

    angle = direction_angles.get(
        direction,
        0
    )

    # Rotate the mouth around the movement direction
    start = angle + mouth
    end = angle + 360 - mouth

    draw.pieslice(
        (
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius
        ),
        start=start,
        end=end,
        fill=YELLOW
    )

    # Eye
    eye_angle = math.radians(
        angle - 45
    )

    eye_x = int(
        cx + math.cos(eye_angle) * 5
    )

    eye_y = int(
        cy + math.sin(eye_angle) * 5
    )

    draw.rectangle(
        (
            eye_x - 2,
            eye_y - 2,
            eye_x + 2,
            eye_y + 2
        ),
        fill=(15, 15, 15)
    )


# ============================================================
# DRAW GHOST
# ============================================================

def draw_ghost(
    draw,
    cx,
    cy,
    color,
    frame
):

    bounce = int(
        2 * math.sin(
            frame * 0.20 + cx
        )
    )

    cy += bounce

    r = 10

    # Head
    draw.ellipse(
        (
            cx - r,
            cy - r,
            cx + r,
            cy + r
        ),
        fill=color
    )

    # Body
    draw.rectangle(
        (
            cx - r,
            cy,
            cx + r,
            cy + 9
        ),
        fill=color
    )

    # Feet
    for offset in (-6, 0, 6):

        draw.polygon(
            (
                (cx + offset - 4, cy + 8),
                (cx + offset, cy + 3),
                (cx + offset + 4, cy + 8)
            ),
            fill=color
        )

    # Eyes
    for offset in (-4, 4):

        draw.ellipse(
            (
                cx + offset - 2,
                cy - 4,
                cx + offset + 2,
                cy
            ),
            fill=WHITE
        )


# ============================================================
# DRAW ACTIVITY CELL
# ============================================================

def draw_activity_cell(
    draw,
    date,
    eaten=False,
    eating_progress=0
):

    count = calendar.get(
        date,
        0
    )

    x, y = cell_position(date)

    # Empty day
    if count <= 0:

        draw.rounded_rectangle(
            (
                x,
                y,
                x + CELL,
                y + CELL
            ),
            radius=3,
            fill=GRID_EMPTY
        )

        return


    # Determine activity intensity
    if count <= 2:
        fill = GREEN_1
    elif count <= 4:
        fill = GREEN_2
    else:
        fill = GREEN_3


    # --------------------------------------------------------
    # EATING ANIMATION
    # --------------------------------------------------------

    if eaten:

        if eating_progress >= 1:

            # Fully consumed
            fill = PANEL

        else:

            # Shrinking pellet
            size = max(
                2,
                int(7 * (1 - eating_progress))
            )

            cx = x + CELL // 2
            cy = y + CELL // 2

            draw.ellipse(
                (
                    cx - size,
                    cy - size,
                    cx + size,
                    cy + size
                ),
                fill=YELLOW_BRIGHT
            )

            return


    # --------------------------------------------------------
    # CELL
    # --------------------------------------------------------

    draw.rounded_rectangle(
        (
            x,
            y,
            x + CELL,
            y + CELL
        ),
        radius=3,
        fill=fill
    )


    # Current streak highlight
    if date in streak_dates:

        draw.rounded_rectangle(
            (
                x - 1,
                y - 1,
                x + CELL + 1,
                y + CELL + 1
            ),
            radius=4,
            outline=YELLOW_BRIGHT,
            width=1
        )


# ============================================================
# BUILD A CONTINUOUS PATH
# ============================================================

# Snake-style traversal across the calendar.
#
# Every row alternates direction, creating a continuous
# left-right / right-left route.

route = []

for weekday in range(7):

    row_dates = [
        d
        for d in dates
        if (d - grid_start).days % 7 == weekday
        and d.year == year
    ]

    if weekday % 2 == 1:
        row_dates.reverse()

    route.extend(row_dates)


# Only active days are targets.
targets = [
    date
    for date in route
    if calendar.get(date, 0) > 0
]


# ============================================================
# PAC-MAN PATH
# ============================================================

# Convert each target into a screen coordinate.

target_points = []

for date in targets:

    x, y = cell_position(date)

    target_points.append(
        (
            x + CELL // 2,
            y + CELL // 2,
            date
        )
    )


# ============================================================
# INTERPOLATION
# ============================================================

def interpolate(
    a,
    b,
    t
):

    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t
    )


def direction_between(
    a,
    b
):

    dx = b[0] - a[0]
    dy = b[1] - a[1]

    if abs(dx) > abs(dy):

        return (
            "right"
            if dx > 0
            else "left"
        )

    return (
        "down"
        if dy > 0
        else "up"
    )


# ============================================================
# ANIMATION SETTINGS
# ============================================================

FRAMES_PER_TARGET = 8
EAT_FRAMES = 3

frames = []


# Intro frames
INTRO_FRAMES = 18


# ============================================================
# INTRO
# ============================================================

for frame in range(INTRO_FRAMES):

    img = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT
        ),
        BG
    )

    draw = ImageDraw.Draw(img)

    draw.text(
        (
            WIDTH // 2 - 145,
            160
        ),
        "LEETCODE",
        font=FONT_TITLE,
        fill=YELLOW
    )

    draw.text(
        (
            WIDTH // 2 - 110,
            220
        ),
        "EAT • SOLVE • REPEAT",
        font=FONT_SUBTITLE,
        fill=MUTED
    )

    # Blinking "READY"
    if frame % 6 < 4:

        draw.text(
            (
                WIDTH // 2 - 45,
                280
            ),
            "READY",
            font=FONT_NORMAL,
            fill=GREEN_3
        )

    frames.append(img)


# ============================================================
# MAIN ANIMATION
# ============================================================

for target_index in range(
    len(target_points)
):

    current = target_points[
        target_index
    ]

    # Determine previous position
    if target_index == 0:

        previous = current

    else:

        previous = target_points[
            target_index - 1
        ]


    x1, y1, _ = previous
    x2, y2, current_date = current


    direction = direction_between(
        previous,
        current
    )


    # --------------------------------------------------------
    # MOVEMENT
    # --------------------------------------------------------

    for local_frame in range(
        FRAMES_PER_TARGET
    ):

        progress = (
            local_frame /
            FRAMES_PER_TARGET
        )

        # Smoothstep interpolation
        smooth = (
            progress *
            progress *
            (3 - 2 * progress)
        )


        px, py = interpolate(
            (x1, y1),
            (x2, y2),
            smooth
        )


        img = Image.new(
            "RGB",
            (
                WIDTH,
                HEIGHT
            ),
            BG
        )

        draw = ImageDraw.Draw(img)


        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

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


        draw.text(
            (390, 35),
            f"🔥 {streak} DAY STREAK",
            font=FONT_STATS,
            fill=YELLOW_BRIGHT
        )

        draw.text(
            (390, 78),
            f"ACTIVE DAYS  {active_days}",
            font=FONT_SUBTITLE,
            fill=GREEN_3
        )

        draw.text(
            (1050, 38),
            username,
            font=FONT_SUBTITLE,
            fill=WHITE
        )

        draw.text(
            (1050, 75),
            str(year),
            font=FONT_SUBTITLE,
            fill=MUTED
        )


        # ----------------------------------------------------
        # PANEL
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                30,
                120,
                WIDTH - 30,
                430
            ),
            radius=10,
            fill=PANEL,
            outline=BLUE,
            width=1
        )


        # ----------------------------------------------------
        # MONTHS
        # ----------------------------------------------------

        month_positions = {}

        for date in dates:

            if (
                date.year == year
                and date.day == 1
            ):

                x, _ = cell_position(
                    date
                )

                month_positions[
                    date.month
                ] = x


        for month, x in month_positions.items():

            month_name = datetime(
                year,
                month,
                1
            ).strftime("%b").upper()

            draw.text(
                (
                    x,
                    137
                ),
                month_name,
                font=FONT_SMALL,
                fill=MUTED
            )


        # ----------------------------------------------------
        # WEEKDAYS
        # ----------------------------------------------------

        weekdays = [
            "MON",
            "TUE",
            "WED",
            "THU",
            "FRI",
            "SAT",
            "SUN"
        ]

        for i, name in enumerate(
            weekdays
        ):

            y = (
                GRID_Y +
                i * STEP
            )

            draw.text(
                (
                    40,
                    y
                ),
                name,
                font=FONT_SMALL,
                fill=MUTED
            )


        # ----------------------------------------------------
        # ACTIVITY GRID
        # ----------------------------------------------------

        for date in dates:

            if date.year != year:
                continue


            # Has this target been eaten?
            eaten = False
            eating_progress = 0


            if date in targets:

                eaten_index = targets.index(
                    date
                )

                if eaten_index < target_index:

                    eaten = True
                    eating_progress = 1

                elif eaten_index == target_index:

                    eaten = True

                    eating_progress = (
                        local_frame /
                        FRAMES_PER_TARGET
                    )


            draw_activity_cell(
                draw,
                date,
                eaten=eaten,
                eating_progress=eating_progress
            )


        # ----------------------------------------------------
        # PAC-MAN
        # ----------------------------------------------------

        draw_pacman(
            draw,
            int(px),
            int(py),
            direction,
            local_frame + target_index
        )


        # ----------------------------------------------------
        # GHOSTS
        # ----------------------------------------------------

        ghost_data = [
            (
                WIDTH - 170,
                165,
                RED
            ),
            (
                WIDTH - 120,
                225,
                PINK
            ),
            (
                WIDTH - 175,
                290,
                CYAN
            )
        ]

        for gx, gy, color in ghost_data:

            draw_ghost(
                draw,
                gx,
                gy,
                color,
                local_frame + target_index
            )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        draw.text(
            (
                45,
                448
            ),
            "PAC-MAN IS EATING YOUR LEETCODE ACTIVITY",
            font=FONT_SMALL,
            fill=WHITE
        )

        draw.text(
            (
                WIDTH - 270,
                448
            ),
            "AUTO UPDATED",
            font=FONT_SMALL,
            fill=GREEN_2
        )


        frames.append(img)


# ============================================================
# END SCREEN
# ============================================================

for frame in range(20):

    img = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT
        ),
        BG
    )

    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle(
        (
            30,
            30,
            WIDTH - 30,
            HEIGHT - 30
        ),
        radius=15,
        fill=PANEL,
        outline=BLUE,
        width=1
    )

    draw.text(
        (
            WIDTH // 2 - 145,
            100
        ),
        "LEVEL COMPLETE",
        font=FONT_TITLE,
        fill=YELLOW
    )

    draw.text(
        (
            WIDTH // 2 - 125,
            180
        ),
        f"🔥 {streak} DAY STREAK",
        font=FONT_STATS,
        fill=YELLOW_BRIGHT
    )

    draw.text(
        (
            WIDTH // 2 - 110,
            230
        ),
        f"{active_days} ACTIVE DAYS",
        font=FONT_SUBTITLE,
        fill=GREEN_3
    )

    draw.text(
        (
            WIDTH // 2 - 125,
            290
        ),
        "KEEP SOLVING!",
        font=FONT_SUBTITLE,
        fill=WHITE
    )

    draw.text(
        (
            WIDTH // 2 - 120,
            360
        ),
        "NEXT RUN LOADING...",
        font=FONT_SMALL,
        fill=MUTED
    )

    frames.append(img)


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Quantize frames to keep GIF size reasonable.
optimized_frames = []

for frame in frames:

    optimized_frames.append(
        frame.quantize(
            colors=128,
            method=Image.Quantize.MEDIANCUT
        )
    )


optimized_frames[0].save(
    OUTPUT_FILE,
    save_all=True,
    append_images=optimized_frames[1:],
    duration=80,
    loop=0,
    optimize=True
)


print()
print("========================================")
print("       PAC-MAN V2 GENERATED")
print("========================================")
print(f"Output : {OUTPUT_FILE}")
print(f"Frames : {len(optimized_frames)}")
print(f"Streak : {streak} days")
print(f"Active : {active_days} days")
print("========================================")