# main.py
# import os
# from io import BytesIO
# from dotenv import load_dotenv
# from fastapi import FastAPI, UploadFile, File
# from fastapi.responses import JSONResponse, HTMLResponse
# from elevenlabs.client import ElevenLabs
# 
# load_dotenv()
# 
# elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
# 
# app = FastAPI(title="Lecture & Lab Transcription")
# 
# ---------------------------
# SIMPLE LOCAL NLP FUNCTIONS
# ---------------------------
# 
# def extract_key_points(text):
    # sentences = text.split(". ")
    # keywords = [
        # "important", "note", "remember", "key",
        # "main", "definition", "means", "therefore"
    # ]
    # return [
        # s for s in sentences
        # if any(k in s.lower() for k in keywords)
    # ]
# 
# def summarize_text(text, max_sentences=5):
    # sentences = text.split(". ")
    # return sentences[:max_sentences]
# 
# ---------------------------
# HOME PAGE
# ---------------------------
# 
# @app.get("/", response_class=HTMLResponse)
# async def home():
    # with open("index.html", "r", encoding="utf-8") as f:
        # return f.read()
# 
# ---------------------------
# TRANSCRIBE ENDPOINT
# ---------------------------
# 
# @app.post("/transcribe")
# async def transcribe_audio(file: UploadFile = File(...)):
    # try:
        # audio_data = BytesIO(await file.read())
# 
        # transcription = elevenlabs.speech_to_text.convert(
            # file=audio_data,
            # model_id="scribe_v2",
            # diarize=True,
            # tag_audio_events=True,
            # language_code="eng",
        # )
# 
        # text = transcription.text
# 
        # key_points = extract_key_points(text)
        # summary = summarize_text(text)
# 
        # return JSONResponse({
            # "transcript": text,
            # "key_points": key_points,
            # "summary": summary
        # })
# 
    # except Exception as e:
        # return JSONResponse({"error": str(e)})
# 
# ---------------------------
# RUN SERVER
# ---------------------------
# 
# if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
# 

# main.py
import os
from io import BytesIO
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fpdf import FPDF
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

# ---- ELEVENLABS SETUP ----
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

app = FastAPI(title="Lecture & Lab Transcription")

# ---- HOME PAGE ----
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# ---- HELPERS ----
def detect_questions(transcript_text):
    lines = transcript_text.split(". ")
    questions = [line for line in lines if "?" in line]
    explanations = [line for line in lines if "?" not in line]
    return questions, explanations

def extract_key_points(text):
    sentences = text.split(". ")
    key_points = [
        s for s in sentences
        if any(word in s.lower() for word in [
            "important", "note", "remember", "key", "main", "definition", "means"
        ])
    ]
    return key_points

def summarize_text(text, max_sentences=5):
    keywords = ["important", "note", "remember", "key", "main", "summary", "definition", "means"]
    sentences = text.split(". ")
    scored = []

    for s in sentences:
        score = sum(1 for kw in keywords if kw in s.lower())
        scored.append((score, s))

    scored.sort(reverse=True)
    summary_sentences = [s for score, s in scored if s][:max_sentences]
    return ". ".join(summary_sentences) + "."

def save_pdf(transcript, key_points, questions, explanations, summary, filename="lecture_summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Lecture Transcription", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"Transcript:\n{transcript}\n")
    pdf.ln(2)

    if key_points:
        pdf.multi_cell(0, 8, "Key Points:\n- " + "\n- ".join(key_points))
        pdf.ln(2)

    if questions:
        pdf.multi_cell(0, 8, "Questions:\n- " + "\n- ".join(questions))
        pdf.ln(2)

    if explanations:
        pdf.multi_cell(0, 8, "Explanations:\n- " + "\n- ".join(explanations))
        pdf.ln(2)

    pdf.multi_cell(0, 8, f"Summary:\n{summary}")
    pdf.output(filename)

    return filename

# ---- TRANSCRIBE ENDPOINT (REAL ELEVENLABS) ----
@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = BytesIO(await file.read())

        transcription = elevenlabs.speech_to_text.convert(
            file=audio_bytes,
            model_id="scribe_v2",
            diarize=True,
            tag_audio_events=True,
            language_code="eng",
        )

        transcript_text = transcription.text

        key_points = extract_key_points(transcript_text)
        questions, explanations = detect_questions(transcript_text)
        summary = summarize_text(transcript_text)

        pdf_file = save_pdf(
            transcript_text,
            key_points,
            questions,
            explanations,
            summary
        )

        return JSONResponse({
            "transcript": transcript_text,
            "key_points": key_points,
            "questions": questions,
            "explanations": explanations,
            "summary": summary,
            "pdf_file": pdf_file
        })

    except Exception as e:
        return JSONResponse({"error": str(e)})

# ---- DOWNLOAD PDF ----
@app.get("/download_pdf")
async def download_pdf():
    file_path = "lecture_summary.pdf"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=file_path)
    return JSONResponse({"error": "PDF not found"})

# ---- RUN SERVER ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)













































































































