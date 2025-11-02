# ESC Validator Templates

This directory contains template images used for symbol detection in the ESC validator.

## Current Templates

### north_arrow.png (To be created)

**Purpose:** Template for detecting north arrow symbols on ESC sheets

**Requirements:**
- Grayscale PNG image
- Size: ~100x100 to 200x200 pixels
- Contains clear north arrow symbol
- High contrast (black symbol on white background preferred)

**How to Create:**

1. The full Page 16 has been extracted to `page16_full.png` (10800 x 7201 pixels at 300 DPI)

2. Several candidate regions have been extracted:
   - `region_top-right_corner.png` - Most likely location
   - `region_upper-right_title_block.png` - Alternative location
   - `region_right_side_upper.png` - Another possibility

3. **Manual Steps:**
   - Open one of the region files in an image viewer
   - Locate the north arrow symbol (typically a compass arrow pointing north)
   - Use an image editor (Paint, GIMP, Photoshop) to crop just the north arrow
   - Crop to approximately 100-200 pixels square
   - Convert to grayscale if needed
   - Save as `north_arrow.png`

4. **Alternative: Use Python script**

```python
from PIL import Image

# Open the region containing the north arrow
region = Image.open('templates/region_top-right_corner.png')

# Manually determine coordinates by visual inspection
# Example: if north arrow is at position (200, 100) with size 150x150
x1, y1 = 200, 100
x2, y2 = x1 + 150, y1 + 150

# Crop the north arrow
north_arrow = region.crop((x1, y1, x2, y2))

# Convert to grayscale
north_arrow = north_arrow.convert('L')

# Save template
north_arrow.save('templates/north_arrow.png')
print('North arrow template created!')
```

## Template Quality Guidelines

**Good Template:**
- Clear, high-contrast symbol
- Minimal background noise
- Symbol is centered in the image
- Appropriate size (not too small, not too large)

**Poor Template:**
- Blurry or low resolution
- Too much surrounding text or graphics
- Symbol is cut off or incomplete
- Very small symbol (<50 pixels)

## Testing Templates

After creating a template, test it with:

```bash
python -m esc_validator.symbol_detector --template templates/north_arrow.png --page 16
```

Expected output:
- Detection: True
- Confidence: >90%
- Location: Coordinates in top-right quadrant

## Future Templates

As the validator evolves, additional templates may be added:
- Specific drainage symbols
- Standard engineering stamps
- Common ESC element symbols

---

**Created:** 2025-11-01
**Last Updated:** 2025-11-01
