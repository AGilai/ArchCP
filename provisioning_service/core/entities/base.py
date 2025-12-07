from pydantic import BaseModel, Field
from typing import Optional

class BaseEntity(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)

    class Config:
        populate_by_name = True