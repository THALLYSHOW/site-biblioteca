from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class Livro(Base):
    __tablename__ = "livros"

    id               = Column(Integer, primary_key=True, index=True)
    titulo           = Column(String,  nullable=False)
    autor            = Column(String,  nullable=False)
    editora          = Column(String,  nullable=False)
    genero           = Column(String,  nullable=False)
    ano_lancamento   = Column(Integer, nullable=True)
    tipo_aquisicao   = Column(String,  default="Compra")
    numero_registro  = Column(String,  unique=True, nullable=False)
    disponivel       = Column(Boolean, default=True)

    emprestimos = relationship("Emprestimo", back_populates="livro")


class Usuario(Base):
    __tablename__ = "usuarios"

    id               = Column(Integer, primary_key=True, index=True)
    nome             = Column(String,  nullable=False)
    telefone         = Column(String,  nullable=False)
    email            = Column(String,  nullable=True)
    documento        = Column(String,  unique=True, nullable=False)
    data_nascimento  = Column(String,  nullable=True)
    endereco         = Column(String,  nullable=True)
    bairro           = Column(String,  nullable=True)
    cidade           = Column(String,  nullable=True)

    emprestimos = relationship("Emprestimo", back_populates="usuario")


class Emprestimo(Base):
    __tablename__ = "emprestimos"

    id             = Column(Integer, primary_key=True, index=True)
    livro_id       = Column(Integer, ForeignKey("livros.id"),   nullable=False)
    usuario_id     = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data_retirada  = Column(String,  nullable=False)
    data_prevista  = Column(String,  nullable=False)
    data_devolvido = Column(String,  nullable=True)
    devolvido      = Column(Boolean, default=False)

    livro   = relationship("Livro",   back_populates="emprestimos")
    usuario = relationship("Usuario", back_populates="emprestimos")


class Evento(Base):
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    data = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    imagem = Column(String, nullable=True)
    legenda = Column(String, nullable=True)
    fotos = Column(Text, nullable=True)