# Hong Kong Written Chinese Neologism Observatory

## Files

- `app.py`: Streamlit application
- `hongkong_written_chinese.json`: lexical and diachronic data
- `requirements.txt`: Python dependencies

## Installation

```bash
cd hk_lexicon_app
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
streamlit run app.py
```

On Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The application reads the JSON file from the same folder as `app.py`.
