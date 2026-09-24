from pathlib import Path
from pypdf import PdfReader


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""

    pdf_path = Path(pdf_path)

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text

if __name__ == "__main__":
    result = extract_text_from_pdf("sample_data/fake_healthcare_claim.pdf")
    print(result)