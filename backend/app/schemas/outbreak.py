from pydantic import BaseModel, ConfigDict, Field


class OutbreakCluster(BaseModel):
    """Example: {"center_lat":12.9716,"center_lng":77.5946,"cases":18}"""

    center_lat: float = Field(ge=-90, le=90)
    center_lng: float = Field(ge=-180, le=180)
    cases: int
    radius_km: int
    window_hours: int
    top_symptoms: list[str]


class OutbreakList(BaseModel):
    """Example: {"outbreaks":[{"center_lat":12.9,"center_lng":77.5,"cases":20}]}"""

    outbreaks: list[OutbreakCluster]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "outbreaks": [
                        {
                            "center_lat": 12.9716,
                            "center_lng": 77.5946,
                            "cases": 20,
                            "radius_km": 5,
                            "window_hours": 48,
                            "top_symptoms": ["fever", "vomiting"],
                        }
                    ]
                }
            ]
        }
    )
