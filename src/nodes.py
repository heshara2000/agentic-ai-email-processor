from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pypdf import PdfReader
from prompts import EXTRACTION_PROMPT
import config
import json

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