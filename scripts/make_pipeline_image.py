from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('figures', exist_ok=True)
W, H = 1400, 600
img = Image.new('RGB', (W, H), 'white')
d = ImageDraw.Draw(img)

# Simple font fallback
try:
    font = ImageFont.truetype('DejaVuSans.ttf', 14)
    title_font = ImageFont.truetype('DejaVuSans.ttf', 20)
except Exception:
    font = ImageFont.load_default()
    title_font = font

# Boxes positions
boxes = [
    ((50, 80), (300, 150), 'Kaggle API\n(src/data_ingestion.py)'),
    ((350, 60), (650, 150), 'Raw data\n(data/)'),
    ((700, 60), (1000, 150), 'ETL / Preprocessing\n(src/preprocessing.py)'),
    ((350, 230), (650, 320), 'Processed data\n(models/processed_data.csv)'),
    ((700, 230), (1000, 320), 'Training\n(src/train_model.py)'),
    ((1100, 60), (1300, 150), 'Airflow DAG\n(dags/ecommerce_pipeline.py)'),
    ((1100, 230), (1300, 320), 'Artefacts\n(models/, mlruns/, figures/)'),
    ((350, 400), (650, 480), 'EDA\n(src/generate_eda.py / figures/)')
]

# draw boxes
for (x1,y1),(x2,y2),text in boxes:
    d.rectangle([x1,y1,x2,y2], outline='#2E75B6', width=2, fill='#E6F0FA')
    # approximate text bounding box using multiline_textbbox if available
    try:
        bbox = d.multiline_textbbox((0,0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        # fallback estimates
        lines = text.split('\n')
        h = 14 * len(lines)
        w = max(len(line) for line in lines) * 7
    tx = x1 + (x2-x1 - w)/2
    ty = y1 + (y2-y1 - h)/2
    d.multiline_text((tx, ty), text, fill='black', font=font, align='center')

# arrows between boxes
def arrow(p1, p2):
    d.line([p1, p2], fill='black', width=2)
    # small arrowhead
    ax, ay = p2
    d.polygon([(ax, ay), (ax-8, ay-6), (ax-8, ay+6)], fill='black')

arrow((300,115),(350,115))
arrow((650,115),(700,115))
arrow((1000,115),(1100,115))
arrow((850,185),(850,230))
arrow((1000,275),(1100,275))
arrow((500,320),(500,400))

# Title
d.text((W/2-180, 10), 'Project-specific ML Pipeline (E-Commerce Behavior)', fill='#1F3870', font=title_font)

img.save('figures/pipeline.png')
print('Saved figures/pipeline.png')
