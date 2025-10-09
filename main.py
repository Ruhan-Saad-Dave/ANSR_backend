from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from routers import alert 

# Create the main FastAPI application instance
app = FastAPI(
    title="My Awesome API",
    description="Backend API for <title>, which will take in the user mobile notification, process and clean the data, and perform various operations.",
    version="1.0.0",
)

# Include the router from the 'items' module
# All routes from items.py will now be available under the /api prefix
app.include_router(alert.alert_router, prefix="/alert")


@app.get("/")
async def root():
    """
    Redirects the user from the root URL ("/") to the documentation URL ("/docs").
    """
    return RedirectResponse(url="/docs")