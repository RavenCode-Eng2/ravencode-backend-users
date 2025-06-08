# 🦉 RavenCode – Módulo de Usuarios

Este repositorio forma parte del proyecto **RavenCode**, una plataforma de aprendizaje interactiva diseñada para enseñar programación a adolescentes de 12 a 16 años. Aquí se encuentra exclusivamente el **módulo de Usuarios**, que gestiona el registro, inicio de sesión, perfiles, roles y preferencias del usuario.

## 🚀 ¿Cómo ejecutar el módulo?

### 🧠 Backend – FastAPI

1. Ir a la carpeta del backend:
```bash
   cd ravencode-backend-users
```
2. Crear entorno virtual:
```bash
   python -m venv venv
```
3. Activar enorno
* En Windows
```bash
   venv\Scripts\activate
```
* En Mac/Linux
```bash
   source venv/bin/activate
```
4. Instalar dependencias
```bash
   pip install -r requirements.txt
```
5. Ejecutar el servidor
```bash
   uvicorn main:app --reload --port 8001
```
6. Verificar en el navegador:
http://localhost:8001/api

### 🔐 Funcionalidades del módulo
Registro de usuarios con validación de campos.

Inicio de sesión con autenticación segura.

Perfiles de usuario con información editable.

Gestión de roles: estudiante, administrador.

Preferencias de interfaz (modo oscuro, notificaciones, etc).

### 👥 Equipo de desarrollo
Proyecto desarrollado por el equipo Cuervos en el curso Ingeniería de Software II – Universidad Nacional de Colombia.

* Diego Felipe Solorzano Aponte

* Laura Valentina Pabon Cabezas

* Diana Valentina Chicuasuque Rodríguez

* Carlos Arturo Murcia Andrade

* Sergio Esteban Rendon Umbarila

* Mateo Andrés Vivas Acosta

* Jorge Andrés Torres Leal

#### Docente: Ing. Camilo Ernesto Vargas Romero
#### Semestre: 2025-1
