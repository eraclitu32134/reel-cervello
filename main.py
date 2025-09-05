from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()

# Permetti richieste da qualsiasi origine (utile per test)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in produzione limita ai tuoi domini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def summarize_text(text: str, max_points=5):
    """Sintesi semplicissima: prime frasi fino a max_points."""
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return sentences[:max_points]

@app.post("/summarize")
async def summarize(
    request: Request,
    source_type: str = Form(...),
    source_url: str = Form(None),
    file: UploadFile = None
):
    # 🔍 Log di debug: vediamo cosa arriva
    form_data = await request.form()
    print("Form ricevuto:", dict(form_data))
    print("Files ricevuti:", list(form_data.keys()))

    text = ""

    if source_type == "url" and source_url:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0 Safari/537.36"
                )
            }
            r = requests.get(source_url, headers=headers, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(separator=" ")
        except Exception as e:
            return {"error": f"Errore nel recupero URL: {e}"}

    elif source_type == "pdf" and file:
        try:
            pdf_bytes = await file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
        except Exception as e:
            return {"error": f"Errore nella lettura PDF: {e}"}

    else:
        return {"error": "Input non valido: specifica 'url' con source_url o 'pdf' con file"}

    if not text.strip():
        return {"error": "Nessun testo estratto dalla sorgente"}

    summary_points = summarize_text(text)
    return {"summary": summary_points}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)