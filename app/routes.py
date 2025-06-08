from fastapi import APIRouter
from app.database import usuarios
from app.models import Usuario

router = APIRouter()

@router.get("/usuarios")
def listar_usuarios():
    return list(usuarios.find({}, {"_id": 0}))

@router.post("/usuarios")
def crear_usuario(usuario: Usuario):
    usuarios.insert_one(usuario.dict())
    return {"mensaje": "Usuario creado"}
