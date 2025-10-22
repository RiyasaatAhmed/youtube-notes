from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="YouTube Notes API",
    description="API for converting YouTube videos into organized notes",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "YouTube Notes API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "youtube-notes-backend"}