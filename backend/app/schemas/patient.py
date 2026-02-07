from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, conint, constr

SupportedLanguage = Literal["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa"]
Gender = Literal["male", "female", "other"]


class PatientCreate(BaseModel):
    """Example: {"phone_number":"9876543210","age":28,"gender":"male","preferred_language":"hi"}"""

    phone_number: constr(pattern=r"^[6-9]\d{9}$") = Field(
        description="10-digit Indian mobile number"
    )
    age: conint(ge=0, le=120)
    gender: Gender
    preferred_language: SupportedLanguage

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "phone_number": "9876543210",
                    "age": 28,
                    "gender": "male",
                    "preferred_language": "hi",
                }
            ]
        }
    )


class PatientUpdate(BaseModel):
    """Example: {"age":30,"preferred_language":"en"}"""

    phone_number: constr(pattern=r"^[6-9]\d{9}$") | None = None
    age: conint(ge=0, le=120) | None = None
    gender: Gender | None = None
    preferred_language: SupportedLanguage | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"age": 30, "preferred_language": "en"},
            ]
        }
    )


class PatientResponse(BaseModel):
    """Example: {"id":"uuid","age":28,"gender":"male","preferred_language":"hi","is_active":true}"""

    id: str
    age: int
    gender: Gender
    preferred_language: SupportedLanguage
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
