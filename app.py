from sqlalchemy import create_engine, Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Base de datos local SQLite
DATABASE_URL = "sqlite:///sigpac.db"

# Motor de base de datos con ajustes para SQLite
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}  # Necesario para SQLite en Flask
)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)

    parcelas = relationship("Parcela", back_populates="usuario")


class Parcela(Base):
    __tablename__ = "parcelas"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"))
    nombre = Column(String)
    provincia = Column(String)
    municipio = Column(String)
    cultivo = Column(String)
    superficie = Column(String)
    geometria = Column(JSON)

    usuario = relationship("Usuario", back_populates="parcelas")


def init_db():
    Base.metadata.create_all(engine)
