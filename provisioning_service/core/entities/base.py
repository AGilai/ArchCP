from pydantic import BaseModel, Field, BeforeValidator
from typing import Optional, Annotated, Any

# 1. Logic: If the value is an ObjectId, convert it to a string
def stringify_object_id(v: Any) -> Any:
    if v and hasattr(v, '__class__') and v.__class__.__name__ == 'ObjectId':
        return str(v)
    return v

# 2. Type Definition: A String that runs the logic above *before* validation
PyObjectId = Annotated[str, BeforeValidator(stringify_object_id)]

class BaseEntity(BaseModel):
    # 3. Usage: The ID field now accepts ObjectId objects and auto-converts them
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    class Config:
        populate_by_name = True