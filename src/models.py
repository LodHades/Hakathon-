
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, JSON, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship

from sqlalchemy import Enum
import enum


class Base(DeclarativeBase):
    pass



