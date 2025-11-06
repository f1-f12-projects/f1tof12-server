from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from scripts.customer.api import router as customer_router
from scripts.users.api import router as users_router
from scripts.spoc.api import router as spoc_router
from scripts.invoices.api import router as invoice_router
from scripts.requirements.api import router as requirements_router
from scripts.profiles.api import router as profiles_router
from scripts.leaves.api import router as leaves_router
from scripts.utils.cloudfront_middleware import CloudFrontMiddleware
from version import __version__, __changelog__
from load_env import load_environment
import logging
import os

# Load environment configuration
load_environment()

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="F1toF12 API", debug=True)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        f"{error['loc'][-1] if error['loc'] else 'field'} is required" if error['type'] == 'missing' else error['msg']
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={"detail": errors[0] if len(errors) == 1 else errors}
    )

# Include routers with customer prefix
customer_prefix = f"/{os.getenv('CUSTOMER', 'f1tof12')}"
routers = [customer_router, users_router, spoc_router, invoice_router, requirements_router, profiles_router, leaves_router]
for router in routers:
    app.include_router(router, prefix=customer_prefix)

# Add CloudFront restriction middleware (only in production)
if os.getenv('ENVIRONMENT') == 'prod':
    app.add_middleware(CloudFrontMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://f1tof12.com", "https://www.f1tof12.com"] if os.getenv('ENVIRONMENT') == 'prod' else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-origin", "x-cloudfront-secret"],
    expose_headers=["X-CloudFront-Secret"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("F1toF12 API starting up")

@app.get(f"/{os.getenv('CUSTOMER', 'f1tof12')}/")
def root():
    return {"message": "F1toF12 API", "version": __version__, "endpoints": ["/vst/login", "/vst/health"]}

@app.get(f"/{os.getenv('CUSTOMER', 'f1tof12')}/version")
def get_version():
    # Get version history to determine type
    versions = list(__changelog__.keys())
    current_version = __version__
    
    # Find previous version
    current_idx = versions.index(current_version) if current_version in versions else 0
    
    if current_idx > 0:
        prev_version = versions[current_idx + 1]  # Next in list (older version)
        curr_parts = [int(x) for x in current_version.split('.')]
        prev_parts = [int(x) for x in prev_version.split('.')]
        
        if curr_parts[0] > prev_parts[0]:
            version_type = "Major"
        elif curr_parts[1] > prev_parts[1]:
            version_type = "Minor"
        else:
            version_type = "Patch"
    else:
        version_type = "Initial"
    
    return {
        "version": __version__,
        "type": version_type,
        "changelog": __changelog__[__version__]
    }

@app.get(f"/{os.getenv('CUSTOMER', 'f1tof12')}/health")
def health_check():
    return {"status": "ok", "message": "F1toF12 API is running", "version": __version__}

