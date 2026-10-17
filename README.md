# Hong Kong Written Chinese Neologism Observatory

**Corpus-Based Lexical Analysis and Diachronic Exploration of Hong Kong Written Chinese**

Developed by **LATHENTIA Technologies**.

## Overview

The Hong Kong Written Chinese Neologism Observatory is a research-oriented computational resource for exploring lexical innovation and diachronic variation in Hong Kong Written Chinese.

The project combines corpus linguistics, natural language processing (NLP), computational lexicography and interactive visualization to support the exploration of lexical and temporal patterns.

It also contributes to ongoing research on structured lexical resources and OntoLex-Lemon-based knowledge representation.

## Research Objectives

- Explore lexical innovation in Hong Kong Written Chinese.
- Investigate diachronic patterns and lexical variation.
- Develop computational methods for lexical data analysis.
- Provide interactive access to lexical and diachronic information.
- Explore the interoperability of lexical resources through OntoLex-Lemon.

## Repository Files

- `app.py`: Streamlit application.
- `hongkong_written_chinese.json`: Lexical and diachronic data.
- `Hong Kong Written Chinese, HKWC.ipynb`: Jupyter Notebook for computational analysis.
- `requirements.txt`: Python dependencies.
- `README.md`: Project documentation.

## Installation

Clone the repository:

```bash
git clone https://github.com/LATHENTIA-Technologies/HK-Chinese-Lexical-Resources.git
cd HK-Chinese-Lexical-Resources
```

Create a virtual environment:

**macOS / Linux**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The application reads the JSON file from the same directory as `app.py`.

## Data Availability

The repository includes selected structured lexical data and research code.

Large-scale source corpora are not necessarily included because of storage requirements and potential copyright or licensing restrictions.

## Acknowledgements

This project builds upon research experience and methodological developments associated with **NeoLex**, particularly in corpus-based neology and computational lexicography.

The author also gratefully acknowledges the scientific exchanges and collaborative research environment of **ENEOLI (European Network on Lexical Innovation)**, a COST Action supporting interdisciplinary research on lexical innovation and neology.

## Author

**Lian Chen, PhD**

**LATHENTIA Technologies**

Language · Knowledge · Intelligence

Website: https://www.lathentia.com/

Email: lian.chen@lathentia.com

## Citation

If you use this project or its resources, please acknowledge the repository and cite the associated research publication when available.

## License

The licensing terms for the source code and lexical data will be specified separately.
