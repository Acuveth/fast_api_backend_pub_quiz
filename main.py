from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from db.database import engine
from db.models import Base as BaseModels
from db.models_menu import Base as BaseMenuModels
from api.routes.auth import router as auth_router
from api.routes.websocket import router as websocket_router
from api.routes.menu import router as menu_router
from api.routes.question import router as question_router
# Create tables if they don't exist
BaseModels.metadata.create_all(bind=engine)
BaseMenuModels.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="PubQuiz API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create static directories if they don't exist
os.makedirs("static/profiles", exist_ok=True)
os.makedirs("static/menu", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(websocket_router)
app.include_router(menu_router)
app.include_router(question_router) 

@app.get("/")
async def root():
    return {"message": "Welcome to PubQuiz API"}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)