from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scripts.customer.api import router as customer_router
from scripts.users.api import router as users_router
from scripts.spoc.api import router as spoc_router
from scripts.invoices.api import router as invoice_router
from version import __version__
import logging

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="F1toF12 API", debug=True)

# Include routers
app.include_router(customer_router)
app.include_router(users_router)
app.include_router(spoc_router)
app.include_router(invoice_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("F1toF12 API starting up")

@app.get("/")
def root():
    return {"message": "F1toF12 API", "version": __version__, "endpoints": ["/login", "/customer/register", "/customer/list", "/spoc/add", "/spoc/list", "/invoices/create", "/invoices/list", "/health"]}

@app.get("/version")
def get_version():
    return {"version": __version__}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "F1toF12 API is running"}

