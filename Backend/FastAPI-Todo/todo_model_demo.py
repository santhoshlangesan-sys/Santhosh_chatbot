"""Small Pydantic model example; keep this filename distinct from the pydantic package."""

from pydantic import BaseModel, Field, field_validator, ValidationError


class ChatRequest(BaseModel):
    id: int
    name:str = Field(min_length=5, max_length=100) 
    is_active: bool=True


try: 
    user1 = ChatRequest(id=1, name="John", is_active=True)
    print(user1)
except ValidationError as e:
    print("Validation error:", e)    
