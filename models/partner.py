from pydantic import BaseModel
from typing import Optional
from odoo.models import Model


class Partner(BaseModel):
    id: Optional[int]
    name: str
    email: Optional[str]
    is_company: bool = False

    @classmethod
    def from_res_partner(cls, p: Model) -> "Partner":
        return Partner(id=p.id, name=p.name, email=p.email, is_company=p.is_company)
