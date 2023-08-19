from adaptapi_fastapi.middleware import AdaptAPIMiddleware
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(AdaptAPIMiddleware)


class ApiInput(BaseModel):
    greeting: str
    user: str


class ApiOutput(BaseModel):
    message: str


@app.get("/api/latest/")
def greet_user(input: ApiInput) -> ApiOutput:
    return ApiOutput(message=f"{input.greeting} {input.user}")
