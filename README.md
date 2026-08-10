# NutriLens Local

100% local packaged-food nutrition label reader using Tesseract OCR and transparent rule-based analysis.

## Features
- Local image OCR
- Text reader fallback
- Ingredient and allergen keyword signals
- Nutrition value extraction
- Explainable audit trail
- CSV batch analysis
- Synthetic demo data
- JSON/CSV exports
- Professional light Streamlit UI
- No cloud AI API

## macOS OCR setup
```bash
brew install tesseract
```

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m py_compile app.py nutrition_engine.py
streamlit run app.py
```

This is educational decision support, not medical advice or allergen certification. Verify the original package label.
