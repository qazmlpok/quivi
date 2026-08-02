#!python3

import os, sys

import math
from PIL import Image
from PIL import ImageDraw

# Generate an animated image that looks like a clock. This is to test animation, to ensure that differing frame delays match the expected behavior
# And, more importantly, that the result is displayed the same as in a web browser (which presumably has everything all figured out)
# The clock will have a total duration of 30s.
# The image consists of:
# - A large circle and a line going from the center to an edge. This is the clock hand. The line moves with the total elapsed time.
# - Marks denoting every 5s (6 in total - which isn't clocklike but it's the same idea)
# - Text in the upper-right stating the duration of this frame
# - A single pixel with value equal to the current frame (intended for test cases)

#Durations are in 10ths of a second, to match GIF delay behavior
#If the sum is less than 300, padding is added to make up the difference.
#Durations less than 2 will be changed to 10 (to match browser behavior, which quivi also emulates)
durations = [
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [50, "5s"],
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [10, "1s (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [2, "Smoother (5s)"],
    [10, "1s"],
    [50, "5s"],
]

width = 800
height = 800


# Should be 'gif', 'png', or 'webp'. PIL doesn't support any other formats.
img_format: str | list[str]
#img_format = 'webp'
img_format = ['gif', 'png', 'webp']

# ---------------------------------------------------
radius = int(min(width, height) * 0.75) / 2

for x in durations:
    if x[0] < 2:
        x[0] = 10
    if (len(x) == 1):
        x.append('')
#

total = sum([x[0] for x in durations])
print("Total duration:", total)
while total < 300:
    if total % 2 == 1:
        durations.append([3, 'Padding'])
        total += 3
        continue
    durations.append([2, 'Padding'])
    total += 2
#

def generate_frame(elapsed: int, frameNo: int, next_delay: int, txt: str) -> Image.Image:
    frame = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(frame, 'L')

    center_x = width/2
    center_y = height/2
    draw.circle((center_x, center_y), radius, outline=0, width=4)

    # Clock hand
    deg = (elapsed / 300) * 2 * math.pi - math.pi / 2
    hand_x = center_x + radius * math.cos(deg) * 0.95
    hand_y = center_y + radius * math.sin(deg) * 0.95
    draw.line([(center_x, center_y),(hand_x, hand_y)], fill=0, width=2)

    # Clock markers every 5s (so 6 in total). Very similar to the clockhand calculation
    for i in range(6):
        deg = (i / 6) * 2 * math.pi - math.pi / 2
        start_x = center_x + radius * math.cos(deg) * 0.97
        end_x = center_x + radius * math.cos(deg) * 1.03
        start_y = center_y + radius * math.sin(deg) * 0.97
        end_y = center_y + radius * math.sin(deg) * 1.03
        draw.line([(start_x, start_y),(end_x, end_y)], fill=0, width=4)

    # Draw elapsed time bottom-right. This can't actually function as a clock since it can't animate separately.
    draw.text((width * 0.85, height * 0.925), f'0:{elapsed//10:02d}.{elapsed%10}', 0, font_size=16)
    draw.text((width * 0.85, height * 0.925 + 20), f'Next: +{next_delay/10:.1f}', 0, font_size=16)

    # Draw specified text, top-right
    if txt:
        draw.text((width * 0.75, height * 0.1), txt, 0, font_size=16)

    # Pixels (intended for automated tests)
    # - draw frame number at 5, 5
    draw.point((5, 5), frameNo)
    # - draw total duration at 5, 6
    draw.point((5, 6), elapsed)

    return frame

count = 0
imgs: list[Image.Image] = []
for i in range(len(durations)):
    data = durations[i]
    imgs.append(generate_frame(count, i, data[0], data[1]))
    count += data[0]

# Save to GIF
#This is in ms.
img_durations = [x[0] * 100 for x in durations]
first = imgs.pop(0)
def save(fmt: str):
    out_filename = f'clock.{fmt}'
    first.save(out_filename, save_all=True, append_images=imgs, loop=0, duration=img_durations)
    print("Wrote: ", out_filename)

if img_format is str:
    save(img_format)
else:
    for x in img_format:
        save(x)