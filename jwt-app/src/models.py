from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    Sequence,
    String,
    Table,
    UniqueConstraint,
)

from constants import UserRole
from database import metadata


user_table = Table(
    'user',
    metadata,
    Column('id', Integer, Sequence('user_id_seq'), nullable=False, index=True, primary_key=True),
    Column('username', String, nullable=False),
    Column('password', String, nullable=False),
    Column('role', Enum(UserRole), nullable=False),
    UniqueConstraint('username'),
)


token_table = Table(
    'token',
    metadata,
    Column('id', Integer, Sequence('token_id_seq'), nullable=False, index=True, primary_key=True),
    Column('username', String, nullable=False),
    Column('refresh_token', String, nullable=False),
    Column('expired_at', DateTime(timezone=False), nullable=False),
)
