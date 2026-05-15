
from PIL import Image
import os

def optimize_logo(input_path, output_path, max_dim=300):
    with Image.open(input_path) as img:
        print(f"Original size: {img.size}")
        
        # Convert to RGB if it has transparency but we don't need it (it's a dark bg)
        # Actually, let's keep it as is if it's RGBA, but the current one seems to have a solid bg.
        if img.mode == 'RGBA':
            # Create a black background to replace transparency if any
            bg = Image.new('RGB', img.size, (0, 0, 0))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Auto-crop (detect non-black areas)
        # This is a bit complex, let's just do a center crop if we know it's 1024x1024
        # and the logo is roughly in the middle.
        # Better: resize first.
        
        w, h = img.size
        new_size = (max_dim, max_dim)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save as WebP (very efficient)
        img.save(output_path, "WEBP", quality=85)
        print(f"Saved optimized logo to {output_path}")
        print(f"New file size: {os.path.getsize(output_path) / 1024:.2f} KB")

if __name__ == "__main__":
    logo_path = "static/images/logo.png"
    if os.path.exists(logo_path):
        optimize_logo(logo_path, "static/images/logo_optimized.webp")
    else:
        print("Logo not found.")
