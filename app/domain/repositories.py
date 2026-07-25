from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models import Profile, TradeEntry, ProductMetadata

class ProfileRepository(ABC):
    @abstractmethod
    async def get_by_id(self, profile_id: str) -> Optional[Profile]:
        pass

    @abstractmethod
    async def update(self, profile: Profile) -> Profile:
        pass

class LedgerRepository(ABC):
    @abstractmethod
    async def get_by_profile(self, profile_id: str) -> List[TradeEntry]:
        pass

    @abstractmethod
    async def create(self, entry: TradeEntry) -> TradeEntry:
        pass

    @abstractmethod
    async def update(self, entry: TradeEntry) -> TradeEntry:
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        pass

class ProductRepository(ABC):
    @abstractmethod
    async def list_all(self) -> List[ProductMetadata]:
        pass

    @abstractmethod
    async def get_by_id(self, product_id: str) -> Optional[ProductMetadata]:
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[ProductMetadata]:
        pass
