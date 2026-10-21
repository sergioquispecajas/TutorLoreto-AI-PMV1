from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.adapters.entrada.api import router

app=FastAPI(title="TutorLoreto AI - PMV1")
app.include_router(router,prefix="/api")
app.mount("/",StaticFiles(directory="frontend",html=True),name="frontend")
