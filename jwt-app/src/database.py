from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine: Engine = None
session_factory = sessionmaker()
Session = scoped_session(session_factory)

metadata = MetaData()


def configure_engine(config):
    global engine, session_factory
    if engine is None:
        engine = create_engine(f'postgresql+psycopg2://{config["POSTGRES_USER"]}:{config["POSTGRES_PASSWORD"]}'
                               f'@{config["POSTGRES_HOST"]}:{config["POSTGRES_PORT"]}/{config["POSTGRES_DB_NAME"]}',
                               convert_unicode=True)
        session_factory.configure(bind=engine)
