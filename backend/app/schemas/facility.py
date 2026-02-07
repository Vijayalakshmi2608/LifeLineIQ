from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, conint

UrgencyLevel = Literal["EMERGENCY", "URGENT", "ROUTINE", "SELF_CARE"]
FacilityType = Literal["PHC", "CHC", "SDH", "DH", "MEDICAL_COLLEGE", "PRIVATE"]


class FacilitySearch(BaseModel):
    """Example: {"user_lat":12.9716,"user_lng":77.5946,"urgency_level":"URGENT"}"""

    user_lat: float = Field(ge=-90, le=90)
    user_lng: float = Field(ge=-180, le=180)
    urgency_level: UrgencyLevel
    radius_km: conint(ge=1, le=200) = 50
    max_results: conint(ge=1, le=50) = 5
    facility_types: list[FacilityType] | None = None
    open_now: bool | None = None
    emergency_only: bool | None = None
    max_wait_minutes: conint(ge=0, le=240) | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_lat": 12.9716,
                    "user_lng": 77.5946,
                    "urgency_level": "URGENT",
                    "radius_km": 20,
                    "max_results": 5,
                }
            ]
        }
    )


class FacilityResponse(BaseModel):
    """Example: {"name":"District Hospital","distance_km":2.3,"is_open_now":true}"""

    id: str
    name: str
    type: FacilityType = Field(alias="facility_type")
    latitude: float
    longitude: float
    address: str
    district: str
    state: str
    pincode: str
    contact_number: str
    emergency_available: bool
    operating_hours: dict | None = None
    specialties: list[str] | None = None
    bed_capacity: int | None = None
    estimated_wait_time: int | None = None
    is_active: bool
    last_updated: str | None = None
    distance_km: float | None = None
    travel_time: int | None = None
    travel_time_mins: int | None = None
    is_open_now: bool | None = None
    directions_url: str | None = None
    call_url: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class FacilityList(BaseModel):
    """Example: {"total_found":2,"search_radius":20,"facilities":[...]}"""

    total_found: int
    search_radius: int
    facilities: list[FacilityResponse]
