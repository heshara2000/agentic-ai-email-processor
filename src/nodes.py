from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pypdf import PdfReader
from prompts import EXTRACTION_PROMPT
from pathlib import Path
import base64
import config
import json

import pandas as pd

llm = ChatOpenAI(
    model=config.OPENAI_MODEL,
    temperature=0,
    api_key=config.OPENAI_API_KEY,
)



def read_pdf(file_path: str):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text



def extract_employee_data(file_path: str):

    text = read_pdf(file_path)

    prompt = f"""
    {EXTRACTION_PROMPT}

    Document:

    {text}
    """

    response = llm.invoke(
        [HumanMessage(content=prompt)]
    )

    return response.content


def _parse_json(raw: str) -> dict:
    """Parse the LLM response into a dict, tolerating ```json fences / stray text."""
    text = raw.strip()
    if text.startswith("```"):
        # strip a ```json ... ``` fence
        text = text.split("```", 2)[1]
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]

    text = text.strip().strip("`").strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # last resort: grab the outermost { ... }
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise


def extract_employee_json(file_path: str) -> dict:
    """Extract onboarding data and return it as a parsed Python dict."""
    return _parse_json(extract_employee_data(file_path))


# ---------------------------------------------------------------------------
# Multi-format support: images (vision) and CSV (bulk), plus a dispatcher.
# ---------------------------------------------------------------------------

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# Map messy CSV headers -> our schema fields.
_CSV_COLUMN_MAP = {
    "employee_name": "employee_name",
    "name": "employee_name",
    "full name": "employee_name",
    "full_name": "employee_name",
    "email": "email",
    "email address": "email",
    "email_address": "email",
    "department": "department",
    "dept": "department",
    "manager": "manager",
    "reporting manager": "manager",
    "reporting_manager": "manager",
    "office": "office",
    "location": "office",
    "office location": "office",
    "office_location": "office",
    "start_date": "start_date",
    "start date": "start_date",
    "joining date": "start_date",
    "joining_date": "start_date",
}


def extract_from_image(file_path: str) -> dict:
    """Read a scanned/photographed form using the LLM's vision capability."""
    raw = Path(file_path).read_bytes()
    b64 = base64.b64encode(raw).decode()
    suffix = Path(file_path).suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    data_url = f"data:image/{mime};base64,{b64}"

    message = HumanMessage(content=[
        {"type": "text", "text": EXTRACTION_PROMPT},
        {"type": "image_url", "image_url": {"url": data_url}},
    ])
    response = llm.invoke([message])
    return _parse_json(response.content)


def read_csv_records(file_path: str) -> list[dict]:
    """Parse a bulk onboarding CSV into one normalized record per row."""
    df = pd.read_csv(file_path, dtype=str).fillna("")
    records: list[dict] = []
    for _, row in df.iterrows():
        record = {
            "employee_name": "",
            "email": "",
            "department": "",
            "manager": "",
            "office": "",
            "start_date": "",
        }
        for column in df.columns:
            key = _CSV_COLUMN_MAP.get(str(column).strip().lower())
            if key:
                record[key] = str(row[column]).strip()
        records.append(record)
    return records


def extract_records(file_path: str) -> list[dict]:
    """Extract one or more employee records from any supported file type.

    Returns a list so a single CSV can yield multiple employees, while a
    PDF or image yields a list with one record. Dispatches on file extension.
    """
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return [extract_employee_json(file_path)]
    if suffix in IMAGE_SUFFIXES:
        return [extract_from_image(file_path)]
    if suffix == ".csv":
        return read_csv_records(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")