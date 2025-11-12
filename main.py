import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from core.setup import initialize_firebase
from routers import alert, prediction, intake, recurring, chatbot

db = initialize_firebase()
# The db object is imported from core.setup where it is initialized.
# If db is None, it means initialization failed, and we should exit.
if not db:
    print("❌ Firebase initialization failed. Exiting application.")
    exit(1)

app = FastAPI(
    title="FinSight API",
    description="API for smart expense tracking and financial insights.",
    version="1.0.0",
)

# Include all the application routers
app.include_router(alert.alert_router, prefix="/alert")
app.include_router(prediction.router, prefix="/prediction")
app.include_router(intake.router, prefix="/intake")
app.include_router(recurring.router, prefix="/recurring")
app.include_router(chatbot.router, prefix="/chatbot")

 
@app.get("/")
async def root():
    """Redirects the root path to the API documentation."""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
