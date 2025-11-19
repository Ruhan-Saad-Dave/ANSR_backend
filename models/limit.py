from pydantic import BaseModel 

class Limit(BaseModel):
    user_id: str
    type: str
    limit: float