from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scripts.db.s3_backup import restore_from_s3
from scripts.customer.api import router as customer_router
from scripts.users.api import router as users_router

app = FastAPI(title="F1toF12 API", debug=True)

# Include routers
app.include_router(customer_router)
app.include_router(users_router)

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
    try:
        restore_from_s3()  # Load database from S3 on startup
    except Exception as e:
        print(f"S3 restore failed on startup: {e}")

@app.get("/")
def root():
    return {"message": "F1toF12 API", "endpoints": ["/register", "/login", "/health", "/users", "/companies", "/companies/{company_id}/status"]}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "F1toF12 API is running"}

