from pydantic import BaseModel 

class Alert(BaseModel):
    id: int 
    limit: int