from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Import settings and health 
from config import settings
#from fastapi import APIRouter
from pydantic import BaseModel
#from datetime import datetime



# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",           # Where to find the instruction manual
    redoc_url="/redoc",         # Alternative instruction manual
    openapi_url="/openapi.json" # Technical specifications
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins, 
    allow_credentials=True,                  
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  
    allow_headers=["*"],                     
)

# Create a router 
# router = APIRouter()

# Define what a health response looks like 
class HealthResponse(BaseModel):
    status: str
    message: str
    #timestamp: str
    version: str


# instruction manual
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Information desk 
@app.get("/info", tags=["Information"])
async def get_app_info():
   
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "documentation": "/docs",
        "alternative_docs": "/redoc",
        "health_check": f"{settings.api_v1_prefix}/health"
    }
    
@app.get("/health", tags=["Health Check"], response_model=HealthResponse)
async def health_check():
    
    return HealthResponse(
        status="healthy",
        message="API is running perfectly!",
       # timestamp=datetime.utc().isoformat() + "Z",
        version="1.0.0"
    )

