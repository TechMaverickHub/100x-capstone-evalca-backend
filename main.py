from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import model as auth_models
from auth import routers as auth_routes
from core.exceptions import register_exception_handlers
from database.session import engine
from evaluation import routers as evaluation_routes
from ocr import routers as ocr_routes

try:
    auth_models.Base.metadata.create_all(bind=engine)
except Exception as e:
    import traceback

    print("Error during table creation:")
    traceback.print_exc()

    print("Error during table creation:")
    traceback.print_exc()

app = FastAPI(title="Eval CA Service", version="0.1.0", debug=True)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
app.include_router(ocr_routes.router, prefix="/ocr", tags=["OCR"])
app.include_router(evaluation_routes.router, prefix="/evaluate", tags=["Evaluation"])


@app.get("/")
def health():
    return {"status": "ok"}
