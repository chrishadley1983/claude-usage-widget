"""Dynamic icon rendering for the system tray - Modernized design."""

from PIL import Image, ImageDraw, ImageFont
import math


# New color palette matching the redesign
COLORS = {
    'bg_dark': (10, 10, 15),  # #0a0a0f
    'card_bg': (18, 18, 26),  # #12121a
    'orange': (255, 140, 66),  # #ff8c42
    'orange_light': (255, 160, 96),  # #ffa060
    'red': (255, 107, 107),  # #FF6B6B
    'blue': (0, 180, 255),  # #00b4ff
    'green': (80, 200, 150),  # #50C896
    'track': (26, 26, 36),  # #1a1a24
    'text_white': (255, 255, 255),
    'text_muted': (102, 102, 102),
}


def get_color_for_percentage(percent: float) -> tuple[int, int, int]:
    """Get color based on usage percentage - updated palette."""
    if percent < 70:
        return COLORS['green']
    elif percent < 90:
        return COLORS['orange']
    else:
        return COLORS['red']


def create_percentage_icon(percent: float, size: int = 64) -> Image.Image:
    """Create an icon showing a percentage value.

    Args:
        percent: Usage percentage (0-100)
        size: Icon size in pixels

    Returns:
        PIL Image object
    """
    # Create transparent background
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Get color based on percentage
    color = get_color_for_percentage(percent)

    # Draw circular background
    padding = 2
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=color
    )

    # Draw percentage text
    text = str(int(percent))

    # Try to use a good font, fall back to default
    font_size = size // 2 if percent < 100 else size // 3
    try:
        font = ImageFont.truetype("segoeui.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 2  # Slight adjustment for visual centering

    # Draw text with slight shadow for better visibility
    draw.text((x + 1, y + 1), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    return image


def create_unknown_icon(size: int = 64) -> Image.Image:
    """Create an icon for unknown/no data state - modern dark theme."""
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Dark background matching the new design
    padding = 2
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=COLORS['card_bg']
    )

    # Draw ring outline
    ring_width = size // 10
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        outline=COLORS['track'],
        width=ring_width
    )

    # Question mark in orange
    try:
        font = ImageFont.truetype("segoeui.ttf", size // 2)
    except OSError:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", size // 2)
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", size // 2)
            except OSError:
                font = ImageFont.load_default()

    text = "?"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 2

    draw.text((x, y), text, fill=COLORS['orange'], font=font)

    return image


def create_progress_ring_icon(percent: float, size: int = 64) -> Image.Image:
    """Create an icon with a progress ring around the percentage - modern design.

    Args:
        percent: Usage percentage (0-100)
        size: Icon size in pixels

    Returns:
        PIL Image object
    """
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    color = get_color_for_percentage(percent)

    # Draw background ring (dark track)
    ring_width = size // 7
    padding = 2
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        outline=COLORS['track'],
        width=ring_width
    )

    # Draw progress arc using pieslice approach for smoother arc
    if percent > 0:
        # Create a temporary image for the arc
        arc_image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        arc_draw = ImageDraw.Draw(arc_image)

        start_angle = -90  # Start from top
        end_angle = -90 + (360 * percent / 100)

        # Draw arc
        arc_draw.arc(
            [padding, padding, size - padding, size - padding],
            start_angle, end_angle,
            fill=color,
            width=ring_width
        )

        # Composite
        image = Image.alpha_composite(image, arc_image)
        draw = ImageDraw.Draw(image)

    # Draw center circle (dark background)
    inner_padding = padding + ring_width + 2
    draw.ellipse(
        [inner_padding, inner_padding, size - inner_padding, size - inner_padding],
        fill=COLORS['bg_dark']
    )

    # Draw percentage text
    text = str(int(percent))
    font_size = (size - 2 * inner_padding) // 2
    try:
        font = ImageFont.truetype("segoeui.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", font_size)
        except OSError:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 1

    draw.text((x, y), text, fill=color, font=font)

    return image


def create_logo_icon(size: int = 64) -> Image.Image:
    """Create a stylized logo icon with speech bubble and heartbeat.

    Args:
        size: Icon size in pixels

    Returns:
        PIL Image object
    """
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Scale factor
    s = size / 100.0

    # Draw speech bubble background
    bubble_color = (42, 64, 96)  # #2a4060
    bubble_outline = (58, 90, 128)  # #3a5a80

    # Simplified bubble shape
    padding = int(5 * s)
    draw.ellipse(
        [padding, padding, size - padding, int(size * 0.85)],
        fill=bubble_color,
        outline=bubble_outline
    )

    # Bubble tail (simplified)
    tail_points = [
        (int(30 * s), int(70 * s)),
        (int(25 * s), int(90 * s)),
        (int(45 * s), int(70 * s))
    ]
    draw.polygon(tail_points, fill=bubble_color)

    # Draw heartbeat line
    line_color = COLORS['orange']
    line_width = max(2, int(3 * s))

    heartbeat_points = [
        (int(15 * s), int(45 * s)),
        (int(30 * s), int(45 * s)),
        (int(38 * s), int(25 * s)),
        (int(50 * s), int(65 * s)),
        (int(62 * s), int(45 * s)),
        (int(80 * s), int(45 * s))
    ]

    draw.line(heartbeat_points, fill=line_color, width=line_width, joint='curve')

    return image


def get_app_icon_path(format: str = 'ico') -> str:
    """Get the path to the app icon file, creating it if needed.

    Args:
        format: 'ico' for Windows icons, 'png' for high-quality notifications

    Returns:
        Path to the icon file
    """
    import os
    import tempfile

    if format == 'png':
        png_path = os.path.join(tempfile.gettempdir(), 'claude_pulse_icon.png')
        if not os.path.exists(png_path):
            # Create a high-res PNG for notifications
            icon = create_logo_icon(256)
            icon.save(png_path, format='PNG')
        return png_path

    ico_path = os.path.join(tempfile.gettempdir(), 'claude_pulse_icon.ico')

    # Create if doesn't exist
    if not os.path.exists(ico_path):
        # Create icon at multiple sizes for Windows
        sizes = [16, 32, 48, 64, 128, 256]
        icons = [create_logo_icon(s) for s in sizes]

        # Save as ICO with multiple sizes
        icons[0].save(
            ico_path,
            format='ICO',
            sizes=[(s, s) for s in sizes],
            append_images=icons[1:]
        )

    return ico_path
