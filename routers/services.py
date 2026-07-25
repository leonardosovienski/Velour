from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models.service import Service, ServiceCategory
from schemas.service import (
    ServiceCategoryCreate, ServiceCategoryResponse,
    ServiceCreate, ServiceUpdate, ServiceResponse,
)

router = APIRouter(tags=["services"])


# ── Categorias ─────────────────────────────────────────────────────────────

cat_router = APIRouter(prefix="/service-categories")


@cat_router.get("", response_model=List[ServiceCategoryResponse])
def list_categories(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(ServiceCategory).all()


@cat_router.post("", response_model=ServiceCategoryResponse, status_code=201)
def create_category(body: ServiceCategoryCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    cat = ServiceCategory(**body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@cat_router.patch("/{cat_id}", response_model=ServiceCategoryResponse)
def update_category(cat_id: int, body: ServiceCategoryCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    cat = db.query(ServiceCategory).filter(ServiceCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    for field, value in body.model_dump().items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


@cat_router.delete("/{cat_id}", status_code=204)
def delete_category(cat_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    cat = db.query(ServiceCategory).filter(ServiceCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    db.delete(cat)
    db.commit()


# ── Serviços ───────────────────────────────────────────────────────────────

svc_router = APIRouter(prefix="/services")


@svc_router.get("", response_model=List[ServiceResponse])
def list_services(
    category_id: int = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(Service).filter(Service.is_active == is_active)
    if category_id:
        q = q.filter(Service.category_id == category_id)
    return q.all()


@svc_router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    svc = db.query(Service).filter(Service.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return svc


@svc_router.post("", response_model=ServiceResponse, status_code=201)
def create_service(body: ServiceCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if not db.query(ServiceCategory).filter(ServiceCategory.id == body.category_id).first():
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    svc = Service(**body.model_dump())
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


@svc_router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(service_id: int, body: ServiceUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    svc = db.query(Service).filter(Service.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(svc, field, value)
    db.commit()
    db.refresh(svc)
    return svc


@svc_router.delete("/{service_id}", status_code=204)
def delete_service(service_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    svc = db.query(Service).filter(Service.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    svc.is_active = False
    db.commit()


router.include_router(cat_router)
router.include_router(svc_router)
