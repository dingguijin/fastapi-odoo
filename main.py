import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from starlette.status import HTTP_201_CREATED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

import sys
sys.path.append('/Users/dingguijin/projects/odoo-15-github/odoo')

import odoo
from odoo.api import Environment
from odoo.exceptions import AccessError, MissingError, AccessDenied

from odoo_api import odoo_env
from models import Partner, User

origins = ["http://localhost:4200"]

app = FastAPI(title="FastAPI-Odoo15 App",
              description="Make Odoo API",
              version="0.0.1"
              )

# CORS
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   )


@app.on_event("startup")
def set_default_executor() -> None:
    from concurrent.futures import ThreadPoolExecutor
    import asyncio

    loop = asyncio.get_running_loop()
    # Tune this according to your requirements !
    loop.set_default_executor(ThreadPoolExecutor(max_workers=5))


@app.on_event("startup")
def initialize_odoo() -> None:
    # Read Odoo config from $ODOO_RC.
    odoo.tools.config.parse_config([])


# ------------- partners


@app.get("/partners", response_model=List[Partner])
def partners(is_company: Optional[bool] = None, env: Environment = Depends(odoo_env)):
    domain = []
    if is_company is not None:
        domain.append(("is_company", "=", is_company))
    partners = env["res.partner"].search(domain)
    return [Partner.from_res_partner(p) for p in partners]


@app.get("/partners/{partner_id}", response_model=Partner)
def get_partner(partner_id: int, env: Environment = Depends(odoo_env)):
    try:
        partner = env["res.partner"].browse(partner_id)
        return Partner.from_res_partner(partner)
    except MissingError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)
    except AccessError:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN)


@app.post("/partners", response_model=Partner, status_code=HTTP_201_CREATED)
def create_partner(partner: Partner, env: Environment = Depends(odoo_env)):
    partner = env["res.partner"].create(
        {
            "name": partner.name,
            "email": partner.email,
            "is_company": partner.is_company,
        }
    )
    return Partner.from_res_partner(partner)


# ------------- user auth


@app.post("/login")
def login_user(user: User, env: Environment = Depends(odoo_env)) -> int:
    """ alter env user from SUPERUSER to current user if login successfully
    """
    user_cls = env["res.users"]
    db = env.registry.db_name
    try:
        uid = user_cls.authenticate(db=db, login=user.login, password=user.password, user_agent_env={})
        env.user = user_cls.browse(uid)
        session_token = ""
        return [uid, session_token]
    except AccessDenied as ad:
        return {"access_denied": ad.args[0]}


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
