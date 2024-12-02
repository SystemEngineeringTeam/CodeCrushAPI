from pydantic import BaseModel
import json


class Crush(BaseModel):
    code: str
    player: str
    
    
class Fix(BaseModel):
    code: str
    
    
class Player(BaseModel):
    player: str