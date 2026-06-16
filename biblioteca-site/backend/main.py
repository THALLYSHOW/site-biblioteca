from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# LIBERAR FRONTEND
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():

    return {"message": "API funcionando"}

# EVENTO 1
@app.get("/evento1")
def evento1():

    return {
        "titulo": "Eventos da BMAA",
        "descricao": "A Biblioteca promove palestras, oficinas culturais e eventos educativos para todas as idades."
    }

# EVENTO 2
@app.get("/evento2")
def evento2():

    return {
        "titulo": "Novos Livros",
        "descricao": "Chegaram novos livros de tecnologia, romance, educação e literatura brasileira."
    }

# EVENTO 3
@app.get("/evento3")
def evento3():

    return {
        "titulo": "Espaço para Estudo",
        "descricao": "Nosso espaço possui ambiente climatizado, silencioso e confortável para leitura e estudos."
    }
    
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# LIBERAR FRONTEND
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LISTA DE LIVROS
@app.get("/livros")
def listar_livros():

    return [

        {
            "titulo": "Dom Casmurro",
            "autor": "Machado de Assis"
        },

        {
            "titulo": "Harry Potter",
            "autor": "J.K Rowling"
        },

        {
            "titulo": "O Pequeno Príncipe",
            "autor": "Antoine de Saint-Exupéry"
        },

        {
            "titulo": "Python para Iniciantes",
            "autor": "João Silva"
        }

    ]