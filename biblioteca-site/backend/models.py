from sqlalchemy import Column, Integer, String
from backend.database import Base

class livro(Base):
    __tablename__ = "livros"
    
    id = Column(Integer, primary_key = True, index=True)
    
    titulo = Column(String)
    autor = Column(String)
    categoria = Column(String)