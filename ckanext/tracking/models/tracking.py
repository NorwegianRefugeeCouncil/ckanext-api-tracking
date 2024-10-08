import logging

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql import func
from sqlalchemy.types import UnicodeText

from ckan import model
from ckan.model.meta import metadata
from ckan.model.types import make_uuid


log = logging.getLogger(__name__)
Base = declarative_base(metadata=metadata)


class TrackingUsage(Base):
    """
    This class is intended to track all CKAN usage with API tokens.
    The CKAN core tracking method is not sufficient for our needs.
    """
    __tablename__ = "tracking_usage"

    id = Column(UnicodeText, primary_key=True, default=make_uuid)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    # We will probably want to track invalid attempts so we allow null for user_id
    user_id = Column(UnicodeText, nullable=True)
    # Do not use enum, leave this open for future use
    # Default options are API | UI + other you can think of (CLI?)
    tracking_type = Column(UnicodeText, nullable=False)
    # optional, show | edit | home
    tracking_sub_type = Column(UnicodeText, nullable=False)
    # For API Token usage, we will store the token name for reference
    # Do not use the ID because token can be deleted and names are in general, informative
    token_name = Column(UnicodeText, nullable=True)
    # Some uses include a traceable object (package, resource, organization, etc)
    object_type = Column(UnicodeText, nullable=True)
    object_id = Column(UnicodeText, nullable=True)
    # More information about the usage
    extras = Column(MutableDict.as_mutable(JSONB), nullable=True)

    def dictize(self):
        dct = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return dct

    def save(self):
        model.Session.add(self)
        model.Session.commit()
        model.Session.refresh(self)
        return self
