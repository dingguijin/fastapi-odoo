from pydantic import BaseModel


class User(BaseModel):
    login: str
    password: str
