# pipeline.py
# Main entry point — Drug Interaction Detection System
# Image upload → auto path extraction → OCR → match


import os
import tkinter as tk
from tkinter import filedialog

from config       import SUPPORTED_FORMATS, MAX_IMAGE_MB
from image_utils  import validate_image
from ocr_engine   import get_text_from_image
from drug_matcher import load_drugbank, build_index, match_drug
from interaction  import load_interactions, check_interaction


def browse_image(drug_num):
    """
    Open file browser popup and return selected image path.
    Path is extracted automatically — user just clicks the image.

    Returns:
      image_path: full path to selected image
      None:       if user cancelled
    """
    root = tk.Tk()
    root.withdraw()
    root.lift()
    root.attributes('-topmost', True)

    print(f"\n   Opening file browser for Drug {drug_num}...")
    print(f"  Select your medicine image in the popup window")

    image_path = filedialog.askopenfilename(
        title=f"Select Drug {drug_num} — Medicine Image",
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"),
            ("All files",   "*.*")
        ]
    )

    root.destroy()

    if image_path:
        # Show just filename (not full path) for cleaner display
        print(f"   Image selected : {os.path.basename(image_path)}")
        print(f"   Full path      : {image_path}")
        return image_path
    else:
        print(f"   No image selected")
        return None


def get_drug_input(drug_num, index):
    """
    Get drug identification from user.
    Two clean options:
      1. Upload image → path auto extracted → OCR → match
      2. Type name    → match directly

    Args:
      drug_num: 1 or 2
      index:    drug search index

    Returns:
      drug_id, drug_name or None, None
    """
    print(f"\n{'─'*55}")
    print(f"   DRUG {drug_num}")
    print(f"{'─'*55}")
    print(f"  1 →  Upload medicine image")
    print(f"  2 →   Type drug name manually")

    choice = input(f"\n  Your choice (1 or 2): ").strip()

    #  Option 1: Image upload 
    if choice == "1":

        # Open popup → user clicks image → path extracted automatically
        image_path = browse_image(drug_num)

        if not image_path:
            print("   No image selected — exiting Drug input")
            return None, None

        # Validate image (size, format)
        if not validate_image(image_path):
            return None, None

        # Extract text from image using OCR
        text = get_text_from_image(image_path, drug_num)

        if not text.strip():
            print("   No text could be extracted from image")
            print("   Try a clearer photo or use text input")
            return None, None

        # Match extracted text to drug database
        matches = match_drug(text, index)

    #  Option 2: Text input 
    elif choice == "2":
        drug_name = input(f"\n  Type Drug {drug_num} name: ").strip()

        if not drug_name:
            print("   No name entered!")
            return None, None

        print(f"\n   Searching for: '{drug_name}'")
        matches = match_drug(drug_name, index)

    else:
        print("   Invalid choice! Enter 1 or 2")
        return None, None

    #  Show identified drug 
    if matches:
        best = matches[0]
        print(f"\n   Drug {drug_num} identified!")
        print(f"     Name  : {best['common_name']}")
        print(f"     ID    : {best['drugbank_id']}")
        print(f"     Match : {best['match_type']} (score={best['score']})")
        return best['drugbank_id'], best['common_name']

    print(f"\n   Could not identify Drug {drug_num}")
    print(f"   Try typing the name manually (option 2)")
    return None, None


def show_interaction_result(drug1_name, drug2_name, result):
    """
    Display final interaction result clearly.

    Args:
      drug1_name: name of first drug
      drug2_name: name of second drug
      result:     dict from check_interaction()
    """
    print("\n" + "═" * 55)
    print("          INTERACTION RESULT")
    print("═" * 55)
    print(f"\n  Drug 1 : {drug1_name}")
    print(f"  Drug 2 : {drug2_name}")
    print()

    if not result['found']:
        print("   NO KNOWN INTERACTION FOUND")
        print("  These drugs appear safe to use together")
        print("  (according to DrugBank database)")
    else:
        print("    INTERACTION FOUND!")
        print(f"\n   Description:")
        desc = result['description']
        # Word wrap at 68 chars for readability
        for i in range(0, len(desc), 68):
            print(f"     {desc[i:i+68]}")

    print()
    print("    Always consult a doctor or pharmacist")
    print("     before combining medications.")
    print("═" * 55)


def run_pipeline():
    """
    Main pipeline — full drug interaction detection system.

    Flow:
      1. Load all databases
      2. Get Drug 1 (image upload or text)
      3. Get Drug 2 (image upload or text)
      4. Check interaction
      5. Show result
    """
    print("\n" + "═" * 55)
    print("    DRUG INTERACTION DETECTION SYSTEM")
    print("═" * 55)
    print(f"   Supported formats : {', '.join(SUPPORTED_FORMATS)}")
    print(f"   Max image size    : {MAX_IMAGE_MB} MB")
    print("═" * 55)

    # Load all databases once at startup
    print("\n Loading databases...")
    df           = load_drugbank()
    index        = build_index(df)
    interactions = load_interactions()
    print(" All databases ready!")

    # Get Drug 1
    drug1_id, drug1_name = get_drug_input(1, index)
    if not drug1_id:
        print("\n Could not identify Drug 1 — exiting.")
        return

    # Get Drug 2
    drug2_id, drug2_name = get_drug_input(2, index)
    if not drug2_id:
        print("\n Could not identify Drug 2 — exiting.")
        return

    # Check interaction between the two drugs
    result = check_interaction(drug1_id, drug2_id, interactions)

    # Display result
    show_interaction_result(drug1_name, drug2_name, result)


if __name__ == "__main__":
    run_pipeline()