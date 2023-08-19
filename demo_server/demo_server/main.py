from adaptapi_fastapi.middleware import AdaptAPIMiddleware
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(AdaptAPIMiddleware)


class ApiInput(BaseModel):
    user: str


@app.get("/api/latest/")
def greet_user(input: ApiInput) -> str:
    return f"Hello {input.user}"
