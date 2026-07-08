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