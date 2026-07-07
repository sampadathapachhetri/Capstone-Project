# ═══════════════════════════════════════════════════════════════
# pipeline.py
# Main entry point — Drug Interaction Detection System
# Image upload → auto path extraction → OCR → match
#
# Loading strategy:
#   - EasyOCR model    : loaded once at ocr_engine import
#   - DrugBank index   : loaded once at module level here
#   - Interactions df  : loaded once at module level here
#   All reused for every request — no reloading
# ═══════════════════════════════════════════════════════════════

import os
import tkinter as tk
from tkinter import filedialog

from config       import SUPPORTED_FORMATS, MAX_IMAGE_MB
from image_utils  import validate_image
from ocr_engine   import get_text_from_image
from drug_matcher import load_drugbank, build_index, match_drug
from interaction  import load_interactions, check_interaction

# ── Load databases ONCE at module level ───────────────────────
# These run when pipeline.py is first imported
# NOT every time run_pipeline() is called
print("\n📂 Loading databases...")
_df           = load_drugbank()
_index        = build_index(_df)
_interactions = load_interactions()
print("✅ All databases ready!")


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

    print(f"\n  📂 Opening file browser for Drug {drug_num}...")
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
        print(f"  ✅ Image selected : {os.path.basename(image_path)}")
        print(f"  📁 Full path      : {image_path}")
        return image_path
    else:
        print(f"  ❌ No image selected")
        return None


def get_drug_input(drug_num):
    """
    Get drug identification from user.
    Uses pre-loaded index — no database reload.

    Two input options:
      1. Upload image → OCR → match
      2. Type name    → match directly

    Args:
      drug_num: 1 or 2

    Returns:
      drug_id, drug_name or None, None
    """
    print(f"\n{'─'*55}")
    print(f"  💊 DRUG {drug_num}")
    print(f"{'─'*55}")
    print(f"  1 → 📸 Upload medicine image")
    print(f"  2 → ⌨️  Type drug name manually")

    choice = input(f"\n  Your choice (1 or 2): ").strip()

    # ── Option 1: Image upload ────────────────────────────────
    if choice == "1":
        image_path = browse_image(drug_num)

        if not image_path:
            print("  ❌ No image selected")
            return None, None

        if not validate_image(image_path):
            return None, None

        text = get_text_from_image(image_path, drug_num)

        if not text.strip():
            print("  ❌ No text extracted from image")
            print("  💡 Try a clearer photo or use text input")
            return None, None

        # Use pre-loaded index (not reloaded)
        matches = match_drug(text, _index)

    # ── Option 2: Text input ──────────────────────────────────
    elif choice == "2":
        drug_name = input(f"\n  Type Drug {drug_num} name: ").strip()

        if not drug_name:
            print("  ❌ No name entered!")
            return None, None

        print(f"\n  🔍 Searching for: '{drug_name}'")
        # Use pre-loaded index (not reloaded)
        matches = match_drug(drug_name, _index)

    else:
        print("  ❌ Invalid choice! Enter 1 or 2")
        return None, None

    # ── Show result ───────────────────────────────────────────
    if matches:
        best = matches[0]
        print(f"\n  ✅ Drug {drug_num} identified!")
        print(f"     Name  : {best['common_name']}")
        print(f"     ID    : {best['drugbank_id']}")
        print(f"     Match : {best['match_type']} "
              f"(score={best['score']})")
        return best['drugbank_id'], best['common_name']

    print(f"\n  ❌ Could not identify Drug {drug_num}")
    print(f"  💡 Try typing the name manually (option 2)")
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
    print("         🔬 INTERACTION RESULT")
    print("═" * 55)
    print(f"\n  Drug 1 : {drug1_name}")
    print(f"  Drug 2 : {drug2_name}")
    print()

    if not result['found']:
        print("  ✅ NO KNOWN INTERACTION FOUND")
        print("  These drugs appear safe to use together")
        print("  (according to DrugBank database)")
    else:
        print("  ⚠️  INTERACTION FOUND!")
        print(f"\n  📋 Description:")
        desc = result['description']
        for i in range(0, len(desc), 68):
            print(f"     {desc[i:i+68]}")

    print()
    print("  ⚕️  Always consult a doctor or pharmacist")
    print("     before combining medications.")
    print("═" * 55)


def run_pipeline():
    """
    Main pipeline — uses pre-loaded databases and model.
    No reloading happens here — everything already in memory.

    Flow:
      1. Get Drug 1 (image or text) → uses _index
      2. Get Drug 2 (image or text) → uses _index
      3. Check interaction          → uses _interactions
      4. Show result
    """
    print("\n" + "═" * 55)
    print("   💊 DRUG INTERACTION DETECTION SYSTEM")
    print("═" * 55)
    print(f"   Supported formats : {', '.join(SUPPORTED_FORMATS)}")
    print(f"   Max image size    : {MAX_IMAGE_MB} MB")
    print("═" * 55)

    # Get Drug 1 (databases already loaded above)
    drug1_id, drug1_name = get_drug_input(1)
    if not drug1_id:
        print("\n❌ Could not identify Drug 1 — exiting.")
        return

    # Get Drug 2
    drug2_id, drug2_name = get_drug_input(2)
    if not drug2_id:
        print("\n❌ Could not identify Drug 2 — exiting.")
        return

    # Check interaction (uses pre-loaded _interactions)
    result = check_interaction(drug1_id, drug2_id, _interactions)

    # Show result
    show_interaction_result(drug1_name, drug2_name, result)


if __name__ == "__main__":
    run_pipeline()