from pydantic import BaseModel 

class Alert(BaseModel):
    id: str
    limit: int