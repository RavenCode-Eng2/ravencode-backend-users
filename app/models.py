from pydantic import BaseModel

class Usuario(BaseModel):
    nombre: str
    correo: str
    rol: str
