import pytesseract
import sys
from PIL import Image, ImageDraw, ImageFont
import io

def create_dummy_image_with_text(text="test", size=(100, 50), lang="eng"):
    """Creates a simple in-memory image with text for testing OCR."""
    img = Image.new('RGB', size, color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        # Try to use a common font, fallback if not found
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    
    # Calculate text size and position
    try:
        # For Pillow >= 9.2.0
        text_bbox = d.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        # Fallback for older Pillow versions
        text_width, text_height = d.textsize(text, font=font)

    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2
    d.text((x, y), text, fill=(0,0,0), font=font)
    
    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return Image.open(io.BytesIO(img_byte_arr))

def check_tesseract_installation():
    print("--- Starting Tesseract Check ---")
    try:
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        print(f"pytesseract.tesseract_cmd set to: {pytesseract.pytesseract.tesseract_cmd}")
        
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract version (via pytesseract): {version}")
        
        languages = pytesseract.get_languages(config='')
        print(f"Available Tesseract languages (via pytesseract.get_languages): {languages}")
        
        if not languages:
            print("Warning: No languages found by pytesseract.get_languages().")
        
        print("\nAttempting basic OCR with English (eng)...")
        dummy_image_eng = create_dummy_image_with_text("Hello", lang="eng")
        try:
            ocr_text_eng = pytesseract.image_to_string(dummy_image_eng, lang='eng', config='--psm 6')
            print(f"OCR result for 'Hello' (eng): '{ocr_text_eng.strip()}'")
            if "hello" not in ocr_text_eng.lower():
                print("Warning: OCR for English test string 'Hello' might not be accurate.")
        except Exception as e_ocr_eng:
            print(f"Error during OCR test (eng): {type(e_ocr_eng).__name__} - {e_ocr_eng}", file=sys.stderr)

        print("\nAttempting basic OCR with Vietnamese (vie)...")
        dummy_image_vie = create_dummy_image_with_text("Chào", lang="vie") # Chữ "Chào"
        try:
            ocr_text_vie = pytesseract.image_to_string(dummy_image_vie, lang='vie', config='--psm 6')
            print(f"OCR result for 'Chào' (vie): '{ocr_text_vie.strip()}'")
            if "chào" not in ocr_text_vie.lower():
                 print("Warning: OCR for Vietnamese test string 'Chào' might not be accurate.")
        except Exception as e_ocr_vie:
            print(f"Error during OCR test (vie): {type(e_ocr_vie).__name__} - {e_ocr_vie}", file=sys.stderr)
            if "Failed loading language" in str(e_ocr_vie) or "TesseractError" in str(type(e_ocr_vie)):
                 print("This likely means the 'vie' language data is missing or not found by Tesseract.", file=sys.stderr)


        print("\n--- Tesseract Check Script Finished ---")
        # Even if OCR tests have warnings, exit 0 if Tesseract itself was found.
        # The main app will handle OCR errors.
        sys.exit(0)

    except pytesseract.TesseractNotFoundError:
        print("TesseractNotFoundError: Tesseract is not installed or not found in your PATH, or tesseract_cmd is incorrect.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during Tesseract check: {type(e).__name__} - {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    check_tesseract_installation()
