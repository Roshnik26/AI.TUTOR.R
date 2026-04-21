import os
import tempfile
from typing import List
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from fastapi import UploadFile

def extract_elements_from_file(file: UploadFile):
    """
    Universally partitions any supported file type into structured elements.
    Supports PDF, TXT, DOCX, etc.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        elements = partition(filename=tmp_path)
        
        chunks = chunk_by_title(
            elements,
            multipage_sections=True,
            combine_text_under_n_chars=500,
            max_characters=1000,
        )
        
        return chunks

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def extract_text_from_file(file: UploadFile) -> str:
    """
    LEGACY support for simple text extraction.
    In the new architecture, we prefer extract_elements_from_file.
    """
    elements = extract_elements_from_file(file)
    return "\n\n".join([str(el) for el in elements])