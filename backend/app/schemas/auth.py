from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class LoginIn(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4, max_length=100)


class LoginOut(BaseModel):
    token: str
    user: UserOut
