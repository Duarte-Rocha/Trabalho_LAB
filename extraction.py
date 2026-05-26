# Ler PDFs
import pdfplumber

# Ler DOCX
from docx import Document


# --- PDF ---
def extract_pdf(file):
    text = ""  # guarda o texto final

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""  # extrai texto da página

    return text  # devolve tudo junto


# --- DOCX ---
def extract_docx(file):
    doc = Document(file)  # abre o DOCX

    # junta todos os parágrafos com quebras de linha
    text = "\n".join(p.text for p in doc.paragraphs)

    return text


# --- TXT ---
def extract_txt(file):
    # lê o ficheiro como texto (UTF-8)
    return file.read().decode("utf-8", errors="ignore")
    
