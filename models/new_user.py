from pydantic import BaseModel 

class NewUser(BaseModel):
    user_id: str