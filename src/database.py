from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from src import models
from src import settings



# ------------------------
# ------------------------


class DatabaseError(Exception):
    """Excepción base para errores de base de datos"""
    pass



class CrudHelper:
    def __init__(self):
        self.engine = create_engine(settings.APP_CONN_STRING)
    
    @contextmanager
    def session_scope(self):
        """
        Context manager para manejar sesiones de base de datos de forma segura
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseError(f"Error en base de datos: {str(e)}") from e
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()


    def create_database(self) -> None:
        """
        Crea todas las tablas en la base de datos
        """
        try:
            models.Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            raise DatabaseError(f"No se pudo crear la base de datos: {str(e)}") from e
        



if __name__=="__main__":
    crud = CrudHelper()
    crud.create_database()

"""
python3 -m src.database


"""