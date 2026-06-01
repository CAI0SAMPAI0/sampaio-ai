from pydantic import BaseModel


class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access: str
    refresh: str


class RefreshIn(BaseModel):
    refresh: str


class ProfileOut(BaseModel):
    id:       int
    username: str
    avatar:   str | None

    model_config = {"from_attributes": True}


class ProfileUpdateOut(BaseModel):
    username: str
    avatar:   str | None


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password:     str