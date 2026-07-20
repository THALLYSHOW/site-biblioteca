"""
Biblioteca Municipal Augusto dos Anjos — API FastAPI
- Token HMAC-SHA256 próprio para autenticação de administrador
- Login direto com e-mail e senha
- Eventos totalmente dinâmicos: CRUD + upload de imagem
- Imagens salvas em ./uploads/ (servidas como arquivos estáticos)
"""

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import hashlib, hmac, base64, json, datetime, os, shutil

from backend.database import engine, get_db, Base
from backend import models

# Cria tabelas e pasta de uploads
Base.metadata.create_all(bind=engine)

# Ajusta colunas novas em bancos SQLite existentes
with engine.connect() as conn:
    for table, col in [("eventos", "fotos"), ("usuarios", "bairro"), ("usuarios", "cidade")]:
        info = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        names = [row[1] for row in info]
        if col not in names:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} TEXT"))
            conn.commit()

os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="Biblioteca Municipal Augusto dos Anjos")

# ── Serve imagens uploadadas como arquivos estáticos ──────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://site-biblioteca.onrender.com",
        "https://biblioteca-frontend-4jao.onrender.com",
        "https://www.bibliotecamunicipalaugustodosanjos.com",
        "https://bibliotecamunicipalaugustodosanjos.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ── CREDENCIAIS ───────────────────────────────────────────────
ADMIN_EMAIL = "bibliotecamunicipalalgusto@gmail.com"
ADMIN_SENHA = "biblioteca2023"
_SECRET     = b"bmaa-hmac-secret-2026"

# ══════════════════════════════════════════════════════════════
# TOKEN HMAC
# ══════════════════════════════════════════════════════════════
def _assinar(p: str) -> str:
    return hmac.new(_SECRET, p.encode(), hashlib.sha256).hexdigest()

def criar_token(email: str) -> str:
    payload = json.dumps({"sub": email, "ts": datetime.datetime.utcnow().isoformat()})
    p64 = base64.urlsafe_b64encode(payload.encode()).decode()
    return f"{p64}.{_assinar(p64)}"

def verificar_token(authorization: str = "") -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token ausente")
    partes = authorization[7:].split(".")
    if len(partes) != 2:
        raise HTTPException(401, "Token malformado")
    p64, sig = partes
    if not hmac.compare_digest(_assinar(p64), sig):
        raise HTTPException(401, "Token inválido")
    try:
        return json.loads(base64.urlsafe_b64decode(p64).decode())["sub"]
    except Exception:
        raise HTTPException(401, "Token inválido")


# ══════════════════════════════════════════════════════════════
# SCHEMAS PYDANTIC
# ══════════════════════════════════════════════════════════════
class LoginEtapa1(BaseModel):
    email: str
    senha: str

class LivroSchema(BaseModel):
    titulo:          str
    autor:           str
    editora:         str
    genero:          str
    ano_lancamento:  Optional[int] = None
    tipo_aquisicao:  Optional[str] = "Compra"
    numero_registro: str

class LivroUpdate(BaseModel):
    titulo:          Optional[str] = None
    autor:           Optional[str] = None
    editora:         Optional[str] = None
    genero:          Optional[str] = None
    ano_lancamento:  Optional[int] = None
    tipo_aquisicao:  Optional[str] = None
    numero_registro: Optional[str] = None

class UsuarioSchema(BaseModel):
    nome:            str
    telefone:        str
    email:           Optional[str] = None
    documento:       str
    data_nascimento: Optional[str] = None
    endereco:        Optional[str] = None
    bairro:          Optional[str] = None
    cidade:          Optional[str] = None

class UsuarioUpdate(BaseModel):
    nome:            Optional[str] = None
    telefone:        Optional[str] = None
    email:           Optional[str] = None
    documento:       Optional[str] = None
    data_nascimento: Optional[str] = None
    endereco:        Optional[str] = None
    bairro:          Optional[str] = None
    cidade:          Optional[str] = None

class EmprestimoSchema(BaseModel):
    livro_id:      int
    usuario_id:    int
    data_prevista: str

class EventoSchema(BaseModel):
    titulo:    str
    tipo:      str
    data:      str
    descricao: str
    imagem:    Optional[str] = None
    legenda:   Optional[str] = None
    fotos:     Optional[List[dict]] = None

class EventoUpdate(BaseModel):
    titulo:    Optional[str] = None
    tipo:      Optional[str] = None
    data:      Optional[str] = None
    descricao: Optional[str] = None
    imagem:    Optional[str] = None
    legenda:   Optional[str] = None
    fotos:     Optional[List[dict]] = None


# ══════════════════════════════════════════════════════════════
# SEED — desativado. Tudo é cadastrado pelo administrador.
# ══════════════════════════════════════════════════════════════
def _seed(db: Session):
    pass


# ══════════════════════════════════════════════════════════════
# HELPERS DE SERIALIZAÇÃO
# ══════════════════════════════════════════════════════════════
def _livro(l):
    return {
        "id": l.id, "titulo": l.titulo, "autor": l.autor,
        "editora": l.editora, "genero": l.genero,
        "ano_lancamento": l.ano_lancamento, "tipo_aquisicao": l.tipo_aquisicao,
        "numero_registro": l.numero_registro, "disponivel": l.disponivel,
    }

def _usuario(u):
    return {
        "id": u.id, "nome": u.nome, "telefone": u.telefone,
        "email": u.email, "documento": u.documento,
        "data_nascimento": u.data_nascimento, "endereco": u.endereco,
        "bairro": u.bairro, "cidade": u.cidade,
    }

def _emprestimo(e):
    return {
        "id": e.id, "livro_id": e.livro_id,
        "livro_titulo":      e.livro.titulo          if e.livro   else "",
        "livro_registro":    e.livro.numero_registro if e.livro   else "",
        "usuario_id": e.usuario_id,
        "usuario_nome":      e.usuario.nome          if e.usuario else "",
        "usuario_documento": e.usuario.documento     if e.usuario else "",
        "data_retirada": e.data_retirada, "data_prevista": e.data_prevista,
        "data_devolvido": e.data_devolvido, "devolvido": e.devolvido,
    }

def _evento(ev):
    # Imagens no frontend ficam na raiz; uploads ficam em /uploads/
    imagem_url = ev.imagem or ""
    if imagem_url and not imagem_url.startswith("http") and not imagem_url.startswith("uploads/"):
        pass  # arquivo local da pasta raiz (ex: eventosite.jpeg)

    fotos = []
    if getattr(ev, "fotos", None):
        try:
            fotos = json.loads(ev.fotos) if isinstance(ev.fotos, str) else ev.fotos
        except Exception:
            fotos = []
    if not fotos and imagem_url:
        fotos = [{"url": imagem_url, "legenda": ev.legenda or ""}]

    return {
        "id": ev.id, "titulo": ev.titulo, "tipo": ev.tipo,
        "data": ev.data, "descricao": ev.descricao,
        "imagem": imagem_url, "legenda": ev.legenda or "",
        "fotos": fotos,
    }


# ══════════════════════════════════════════════════════════════
# ROTAS
# ══════════════════════════════════════════════════════════════

@app.get("/")
def home():
    return {"message": "API Biblioteca Municipal Augusto dos Anjos — online"}


# ── LOGIN ─────────────────────────────────────────────────────

@app.post("/login")
def login(dados: LoginEtapa1):
    if dados.email.strip().lower() != ADMIN_EMAIL.lower() or dados.senha != ADMIN_SENHA:
        raise HTTPException(401, "E-mail ou senha incorretos")
    return {"status": "ok", "token": criar_token(ADMIN_EMAIL)}


# ── UPLOAD DE IMAGEM ──────────────────────────────────────────

@app.post("/admin/upload")
async def upload_imagem(
    file: UploadFile = File(...),
    authorization: str = Header(default="")
):
    verificar_token(authorization)
    extensoes_ok = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in extensoes_ok:
        raise HTTPException(400, f"Formato não permitido. Use: {', '.join(extensoes_ok)}")
    # Nome único para evitar colisões
    nome = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    caminho = os.path.join("uploads", nome)
    with open(caminho, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"uploads/{nome}", "nome": nome}


# ── EVENTOS (público) ─────────────────────────────────────────

@app.get("/eventos")
def listar_eventos(db: Session = Depends(get_db)):
    _seed(db)
    return [_evento(e) for e in db.query(models.Evento).order_by(models.Evento.data.desc()).all()]

@app.get("/eventos/{evento_id}")
def detalhe_evento(evento_id: int, db: Session = Depends(get_db)):
    ev = db.query(models.Evento).filter(models.Evento.id == evento_id).first()
    if not ev:
        raise HTTPException(404, "Evento não encontrado")
    return _evento(ev)


# ── EVENTOS (admin CRUD) ──────────────────────────────────────

@app.post("/admin/upload-multiplo")
def upload_multiplo(files: List[UploadFile] = File(...), authorization: str = Header(default="")):
    verificar_token(authorization)
    if len(files) > 10:
        raise HTTPException(400, "Máximo de 10 fotos")
    extensoes_ok = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    urls = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in extensoes_ok:
            raise HTTPException(400, f"Formato não permitido. Use: {', '.join(extensoes_ok)}")
        nome = f"{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{file.filename}"
        caminho = os.path.join("uploads", nome)
        with open(caminho, "wb") as f:
            shutil.copyfileobj(file.file, f)
        urls.append(f"uploads/{nome}")
    return {"urls": urls}

@app.post("/admin/eventos", status_code=201)
def criar_evento(ev: EventoSchema,
                 authorization: str = Header(default=""),
                 db: Session = Depends(get_db)):
    verificar_token(authorization)
    if ev.fotos and len(ev.fotos) > 10:
        raise HTTPException(400, "Máximo de 10 fotos por evento")
    data = ev.dict()
    if ev.fotos is not None:
        data["fotos"] = json.dumps(ev.fotos)
    novo = models.Evento(**data)
    db.add(novo); db.commit(); db.refresh(novo)
    return {"mensagem": "Evento cadastrado", "id": novo.id}

@app.put("/admin/eventos/{evento_id}")
def editar_evento(evento_id: int, dados: EventoUpdate,
                  authorization: str = Header(default=""),
                  db: Session = Depends(get_db)):
    verificar_token(authorization)
    ev = db.query(models.Evento).filter(models.Evento.id == evento_id).first()
    if not ev: raise HTTPException(404, "Evento não encontrado")
    for k, v in dados.dict(exclude_none=True).items():
        if k == "fotos":
            if v is not None and len(v) > 10:
                raise HTTPException(400, "Máximo de 10 fotos por evento")
            setattr(ev, k, json.dumps(v) if v is not None else None)
        else:
            setattr(ev, k, v)
    db.commit()
    return {"mensagem": "Evento atualizado"}

@app.delete("/admin/eventos/{evento_id}")
def deletar_evento(evento_id: int,
                   authorization: str = Header(default=""),
                   db: Session = Depends(get_db)):
    verificar_token(authorization)
    ev = db.query(models.Evento).filter(models.Evento.id == evento_id).first()
    if not ev: raise HTTPException(404, "Evento não encontrado")
    try:
        db.delete(ev)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erro ao remover evento: {str(e)}")
    return {"mensagem": "Evento removido"}


# ── LIVROS (público) ──────────────────────────────────────────

@app.get("/livros")
def listar_livros(db: Session = Depends(get_db)):
    return [_livro(l) for l in db.query(models.Livro).all()]


# ── LIVROS (admin CRUD) ───────────────────────────────────────

@app.post("/admin/livros", status_code=201)
def criar_livro(livro: LivroSchema,
                authorization: str = Header(default=""),
                db: Session = Depends(get_db)):
    verificar_token(authorization)
    if db.query(models.Livro).filter(models.Livro.numero_registro == livro.numero_registro).first():
        raise HTTPException(400, "Número de registro já cadastrado")
    novo = models.Livro(**livro.dict())
    db.add(novo); db.commit(); db.refresh(novo)
    return {"mensagem": "Livro cadastrado", "id": novo.id}

@app.put("/admin/livros/{livro_id}")
def editar_livro(livro_id: int, dados: LivroUpdate,
                 authorization: str = Header(default=""),
                 db: Session = Depends(get_db)):
    verificar_token(authorization)
    l = db.query(models.Livro).filter(models.Livro.id == livro_id).first()
    if not l: raise HTTPException(404, "Livro não encontrado")
    for k, v in dados.dict(exclude_none=True).items():
        setattr(l, k, v)
    db.commit()
    return {"mensagem": "Livro atualizado"}

@app.delete("/admin/livros/{livro_id}")
def deletar_livro(livro_id: int,
                  authorization: str = Header(default=""),
                  db: Session = Depends(get_db)):
    verificar_token(authorization)
    l = db.query(models.Livro).filter(models.Livro.id == livro_id).first()
    if not l: raise HTTPException(404, "Livro não encontrado")
    # Deletar emprestimos relacionados antes de apagar o livro (comportamento em cascata)
    try:
        emprestimos = db.query(models.Emprestimo).filter(models.Emprestimo.livro_id == livro_id).all()
        for emp in emprestimos:
            # se houver referência ao livro, apenas remova o empréstimo
            db.delete(emp)
        db.delete(l)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erro ao remover livro: {str(e)}")
    return {"mensagem": "Livro e empréstimos relacionados removidos"}


# ── USUÁRIOS (admin CRUD) ─────────────────────────────────────

@app.get("/admin/usuarios")
def listar_usuarios(authorization: str = Header(default=""),
                    db: Session = Depends(get_db)):
    verificar_token(authorization)
    return [_usuario(u) for u in db.query(models.Usuario).all()]

@app.post("/admin/usuarios", status_code=201)
def criar_usuario(usuario: UsuarioSchema,
                  authorization: str = Header(default=""),
                  db: Session = Depends(get_db)):
    verificar_token(authorization)
    if db.query(models.Usuario).filter(models.Usuario.documento == usuario.documento).first():
        raise HTTPException(400, "CPF/RG já cadastrado")
    novo = models.Usuario(**usuario.dict())
    db.add(novo); db.commit(); db.refresh(novo)
    return {"mensagem": "Usuário cadastrado", "id": novo.id}

@app.put("/admin/usuarios/{uid}")
def editar_usuario(uid: int, dados: UsuarioUpdate,
                   authorization: str = Header(default=""),
                   db: Session = Depends(get_db)):
    verificar_token(authorization)
    u = db.query(models.Usuario).filter(models.Usuario.id == uid).first()
    if not u: raise HTTPException(404, "Usuário não encontrado")
    for k, v in dados.dict(exclude_none=True).items():
        setattr(u, k, v)
    db.commit()
    return {"mensagem": "Usuário atualizado"}

@app.delete("/admin/usuarios/{uid}")
def deletar_usuario(uid: int,
                    authorization: str = Header(default=""),
                    db: Session = Depends(get_db)):
    verificar_token(authorization)
    u = db.query(models.Usuario).filter(models.Usuario.id == uid).first()
    if not u: raise HTTPException(404, "Usuário não encontrado")
    # Deletar emprestimos relacionados antes de apagar o usuário (comportamento em cascata)
    try:
        emprestimos = db.query(models.Emprestimo).filter(models.Emprestimo.usuario_id == uid).all()
        for emp in emprestimos:
            # se o empréstimo estiver associado a um livro, marque o livro como disponível
            if emp.livro:
                emp.livro.disponivel = True
            db.delete(emp)
        db.delete(u)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erro ao remover usuário: {str(e)}")
    return {"mensagem": "Usuário e empréstimos relacionados removidos"}


# ── EMPRÉSTIMOS ───────────────────────────────────────────────

@app.get("/admin/emprestimos")
def listar_emprestimos(authorization: str = Header(default=""),
                       db: Session = Depends(get_db)):
    verificar_token(authorization)
    return [_emprestimo(e) for e in db.query(models.Emprestimo).all()]

@app.post("/admin/emprestimos", status_code=201)
def criar_emprestimo(dados: EmprestimoSchema,
                     authorization: str = Header(default=""),
                     db: Session = Depends(get_db)):
    verificar_token(authorization)
    livro = db.query(models.Livro).filter(models.Livro.id == dados.livro_id).first()
    if not livro:            raise HTTPException(404, "Livro não encontrado")
    if not livro.disponivel: raise HTTPException(400, "Livro já está emprestado")
    usuario = db.query(models.Usuario).filter(models.Usuario.id == dados.usuario_id).first()
    if not usuario:          raise HTTPException(404, "Usuário não encontrado")
    hoje = datetime.date.today().isoformat()
    emp = models.Emprestimo(
        livro_id=dados.livro_id, usuario_id=dados.usuario_id,
        data_retirada=hoje, data_prevista=dados.data_prevista, devolvido=False
    )
    livro.disponivel = False
    db.add(emp); db.commit(); db.refresh(emp)
    return {"mensagem": "Empréstimo registrado", "id": emp.id}

@app.post("/admin/emprestimos/{emp_id}/devolver")
def devolver(emp_id: int,
             authorization: str = Header(default=""),
             db: Session = Depends(get_db)):
    verificar_token(authorization)
    emp = db.query(models.Emprestimo).filter(models.Emprestimo.id == emp_id).first()
    if not emp:       raise HTTPException(404, "Empréstimo não encontrado")
    if emp.devolvido: raise HTTPException(400, "Já devolvido")
    emp.devolvido = True
    emp.data_devolvido = datetime.date.today().isoformat()
    if emp.livro:
        emp.livro.disponivel = True
    db.commit()
    return {"mensagem": "Devolução registrada"}


@app.delete("/admin/emprestimos/{emp_id}")
def deletar_emprestimo(emp_id: int,
                      authorization: str = Header(default=""),
                      db: Session = Depends(get_db)):
    verificar_token(authorization)
    emp = db.query(models.Emprestimo).filter(models.Emprestimo.id == emp_id).first()
    if not emp:
        raise HTTPException(404, "Empréstimo não encontrado")
    try:
        if emp.livro:
            emp.livro.disponivel = True
        db.delete(emp)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Erro ao remover empréstimo: {str(e)}")
    return {"mensagem": "Empréstimo removido"}