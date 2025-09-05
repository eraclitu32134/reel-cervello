from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()

# Permetti richieste da qualsiasi origine (per test su Snack)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in produzione limita ai tuoi domini
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def summarize_text(text: str, max_points=5):
    # Sintesi semplicissima: prime frasi
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return sentences[:max_points]

@app.post("/summarize")
async def summarize(
    source_type: str = Form(...),
    source_url: str = Form(None),
    file: UploadFile = None
):
    text = ""

    if source_type == "url" and source_url:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0 Safari/537.36"
            )
        }
        r = requests.get(source_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator=" ")

    elif source_type == "pdf" and file:
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)

    else:
        return {"error": "Invalid input"}

    summary_points = summarize_text(text)
    return {"summary": summary_points}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
