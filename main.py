import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from core.setup import initialize_supabase
from routers import limit, intake, chatbot, test, supa
from routers.vault import prediction, recurring

db = initialize_supabase()
# The db object is imported from core.setup where it is initialized.
# If db is None, it means initialization failed, and we should exit.
if not db:
    print("❌ Firebase initialization failed. Exiting application.")
    exit(1)

tags_metadata = [
    {
        "name": "Spending Limit",
        "description": "Endpoints for changing the user's spending limit",
    },
    {
        "name": "Intake",
        "description": "Endpoints for receiving transaction data and storing it in the database.",
    },
    {
        "name": "Chatbot",
        "description": "Endpoints for interacting with the financial chatbot.",
    },
    {
        "name": "test",
        "description": "Testing endpoints for development purposes.",
    },
    {
        "name": "supabase",
        "description": "Endpoints for Supabase database interactions.",
    },
]

app = FastAPI(
    title="FinSight API",
    description="API for smart expense tracking and financial insights.",
    version="1.1.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include all the application routers
app.include_router(limit.router, prefix="/Spending_Limit")
#app.include_router(prediction.router, prefix="/prediction")  #need some work
app.include_router(intake.router, prefix="/intake")
#app.include_router(recurring.router, prefix="/recurring") #need some work
app.include_router(chatbot.router, prefix="/chatbot")
app.include_router(test.router, prefix="/test")
app.include_router(supa.router, prefix="/supabase")

 
@app.get("/")
async def root():
    """Redirects the root path to the API documentation."""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
