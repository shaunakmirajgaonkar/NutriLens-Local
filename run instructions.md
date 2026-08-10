# Run Instructions

```bash
brew install tesseract
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m py_compile app.py nutrition_engine.py
streamlit run app.py
```
