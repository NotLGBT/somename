from .mixins import GeneralBaseMixin


class BaseSharedModel(GeneralBaseMixin):
    """
    Abstact class for SharedModel functionality
    """
    __abstract__ = True
    __tablename__ = None 

    services: list[str] = None
    related_entities: tuple[str] = None 
    shared_type: str = None  
