from pydantic import BaseModel, Field

# ==========================================
# ENDPOINT 1: The Index (/api/v1/user/order)
# ==========================================

class OrderKey(BaseModel):
    """ Represents a single item from the master index list"""
    gamekey: str


# ==========================================
# ENDPOINT 2: The Details (/api/v1/order/{key})
# ==========================================

class DownloadUrl(BaseModel):
    web: str | None = None

class DownloadStruct(BaseModel):
    """ Represents the download struct for a single gamekey"""
    name: str
    url: DownloadUrl | None = None

class DownloadInfo(BaseModel):
    platform: str
    download_struct: list[DownloadStruct] = Field(default_factory=list)

class Subproduct(BaseModel):
    """ Represents a subproduct (e.g. a Steam key)"""
    name: str = Field(alias="human_name")
    downloads: list[DownloadInfo] = Field(default_factory=list)

class Product(BaseModel):
    category: str | None = None
    bundle_name: str = Field(alias="human_name")

class OrderDetails(BaseModel):
    """ Represents the details of a single gamekey"""
    gamekey: str
    product: Product
    amount_spent: float | None = None
    currency: str | None = None
    subproducts: list[Subproduct] = Field(default_factory=list)
