from pydantic import BaseModel 

class Limit(BaseModel):
    user_id: str
    limit_type: str
    limit: float