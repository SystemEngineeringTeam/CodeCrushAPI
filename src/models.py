from pydantic import BaseModel
import json


class Crush(BaseModel):
    code: str
    player: str
    
    
class Code(BaseModel):
    code: str
    
    
class Player(BaseModel):
    player: str
    
class Language(BaseModel):
    player: str
    language: str
    
# class StatusUpdate(BaseModel):
#     player: str  # "player1" または "player2"