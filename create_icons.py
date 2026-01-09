"""Create extension icons - Modernized design matching the new UI."""
from PIL import Image, ImageDraw


def create_icon(size):
    """Create a Claude Pulse icon with speech bubble and heartbeat design."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Scale factor
    s = size / 128.0

    # Colors
    bubble_color = (42, 64, 96)  # #2a4060
    bubble_outline = (58, 90, 128)  # #3a5a80
    orange = (255, 140, 66)  # #ff8c42
    blue = (0, 180, 255)  # #00b4ff

    # Draw speech bubble background (ellipse)
    padding = int(8 * s)
    bubble_bottom = int(size * 0.78)
    draw.ellipse(
        [padding, padding, size - padding, bubble_bottom],
        fill=bubble_color,
        outline=bubble_outline,
        width=max(1, int(2 * s))
    )

    # Bubble tail
    tail_points = [
        (int(35 * s), int(bubble_bottom - 5 * s)),
        (int(28 * s), int(size - 5 * s)),
        (int(50 * s), int(bubble_bottom - 5 * s))
    ]
    draw.polygon(tail_points, fill=bubble_color)

    # Draw heartbeat line with gradient effect
    line_width = max(2, int(4 * s))
    center_y = int(45 * s)

    # Blue to orange gradient heartbeat
    heartbeat_points = [
        (int(18 * s), center_y),
        (int(38 * s), center_y),
        (int(48 * s), int(25 * s)),
        (int(64 * s), int(70 * s)),
        (int(78 * s), center_y),
        (int(110 * s), center_y)
    ]

    # Draw blue part (first half)
    blue_points = heartbeat_points[:3]
    if len(blue_points) >= 2:
        draw.line(blue_points, fill=blue, width=line_width, joint='curve')

    # Draw orange part (second half)
    orange_points = heartbeat_points[2:]
    if len(orange_points) >= 2:
        draw.line(orange_points, fill=orange, width=line_width, joint='curve')

    return img


def create_simple_icon(size):
    """Create a simple progress ring icon for smaller sizes."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors
    bg_dark = (18, 18, 26)
    orange = (255, 140, 66)
    track = (40, 40, 50)

    # Draw background circle
    padding = 2
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=bg_dark,
        outline=track,
        width=max(1, size // 16)
    )

    # Draw partial progress ring
    ring_width = max(2, size // 8)
    draw.arc(
        [padding, padding, size - padding, size - padding],
        -90, 180,  # 75% progress
        fill=orange,
        width=ring_width
    )

    return img


# Create icons directory icons
sizes = [(16, 'simple'), (48, 'full'), (128, 'full')]
for size, style in sizes:
    if style == 'simple' and size < 32:
        icon = create_simple_icon(size)
    else:
        icon = create_icon(size)
    icon.save(f'extension/icons/icon{size}.png')
    print(f'Created icon{size}.png')

print('Done!')
