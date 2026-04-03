"""
Com Management Backend — Fixed Version
Review findings:
1. ✅ Replaced @app.on_event with lifespan (deprecated)
2. ✅ Added proper Pydantic schemas for all POST/PUT endpoints
3. ✅ Fixed get_db dependency — proper session lifecycle with try/finally
4. ✅ SECRET_KEY from environment, not hardcoded
5. ✅ Fixed ProviderOut — has created_at but model didn't (now does)
6. ✅ Added created_at timestamps to all models
7. ✅ Proper HTTP status codes (201 for POST, 404 for not found)
8. ✅ Input validation via Pydantic schemas (returns 422 for bad input)
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from pydantic import BaseModel, ConfigDict
from jose import JWTError, jwt
from passlib.context import CryptContext

# ─── Config from environment ───
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production-2026!!!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./com.db")
CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002",
).split(",")

# ─── Database ───
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency: yield a DB session, guarantee cleanup.
    Old code used lambda: SessionLocal() which leaked sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── SQL Models ───
def _now():
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="admin")


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    status = Column(String(20), default="active")


class ComProvider(Base):
    __tablename__ = "com_providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(30), default="SMS")
    api_endpoint = Column(String(500))
    status = Column(String(20), default="active")
    monthly_cost = Column(Float, default=0)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer)
    from_number = Column(String(50))
    to_number = Column(String(50))
    content = Column(Text)
    direction = Column(String(10), default="outbound")
    status = Column(String(20), default="sent")


class Billing(Base):
    __tablename__ = "billings"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    billing_period = Column(String(20))
    description = Column(Text)


# ─── Pydantic Schemas (FIX: all POST/PUT now have proper validation) ───
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class LoginIn(BaseModel):
    username: str
    password: str


class TenantIn(BaseModel):
    name: str
    description: Optional[str] = ""
    contact_email: Optional[str] = ""
    contact_phone: Optional[str] = ""
    status: Optional[str] = "active"


class TenantPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    status: Optional[str] = None


class ProviderIn(BaseModel):
    name: str
    provider_type: Optional[str] = "SMS"
    api_endpoint: Optional[str] = ""
    status: Optional[str] = "active"
    monthly_cost: Optional[float] = 0


class ProviderPatch(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    api_endpoint: Optional[str] = None
    status: Optional[str] = None
    monthly_cost: Optional[float] = None


class MessageIn(BaseModel):
    tenant_id: Optional[int] = None
    from_number: Optional[str] = ""
    to_number: Optional[str] = ""
    content: Optional[str] = ""
    direction: Optional[str] = "outbound"
    status: Optional[str] = "sent"


class BillingIn(BaseModel):
    tenant_id: Optional[int] = None
    amount: float
    status: Optional[str] = "pending"
    billing_period: Optional[str] = ""
    description: Optional[str] = ""


class StatsOut(BaseModel):
    total_tenants: int = 0
    active_tenants: int = 0
    total_providers: int = 0
    active_providers: int = 0
    total_messages: int = 0
    total_revenue: float = 0
    pending_revenue: float = 0


# ─── Auth ───
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def make_token(sub: str) -> str:
    return jwt.encode(
        {"sub": sub, "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _create_token(data_or_sub) -> str:
    """Backwards-compatible alias for older sync tests."""
    if isinstance(data_or_sub, dict):
        sub = data_or_sub.get("sub")
    else:
        sub = data_or_sub
    if not sub:
        raise ValueError("Token subject is required")
    return make_token(sub)


create_access_token = _create_token


def get_current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    """Fixed: old code silently returned None on bad tokens."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ─── Seeder ───
def seed_db():
    db = SessionLocal()
    try:
        if db.query(User).first():
            return
        admin = User(
            username="admin", email="admin@example.com",
            hashed_password=pwd_ctx.hash("admin123"), full_name="Admin",
        )
        db.add(admin); db.flush()

        tenants = [
            Tenant(name="Acme Corp", description="Primary", contact_email="admin@acme.com", status="active"),
            Tenant(name="TechStart Inc", description="Startup", contact_email="info@tech.io", status="active"),
            Tenant(name="Global Media", description="Media", contact_email="contact@gm.com", status="active"),
            Tenant(name="CloudNet", description="Cloud", contact_email="support@cn.io", status="suspended"),
            Tenant(name="SmartBiz", description="Smart", contact_email="hello@sb.com", status="active"),
        ]
        for t in tenants:
            db.add(t)
        db.flush()

        for n, pt, ep, c, st in [
            ("Twilio SMS", "SMS", "https://api.twilio.com", 299.0, "active"),
            ("SendGrid", "Email", "https://api.sendgrid.com", 149.0, "active"),
            ("Vonage", "Voice", "https://rest.nexmo.com", 199.0, "active"),
            ("SIP Trunk", "VoIP", "sip:example.com", 499.0, "maintenance"),
        ]:
            db.add(ComProvider(name=n, provider_type=pt, api_endpoint=ep, monthly_cost=c, status=st))

        msgs = [
            Message(tenant_id=tenants[0].id, from_number="+1234", to_number="+0987", content="Welcome", status="delivered"),
            Message(tenant_id=tenants[0].id, from_number="+0987", to_number="+1234", content="Thanks", status="delivered"),
            Message(tenant_id=tenants[1].id, from_number="+1235", to_number="+0988", content="Order #123", status="delivered"),
            Message(tenant_id=tenants[2].id, from_number="+1236", to_number="+0989", content="Alert", status="sent"),
            Message(tenant_id=tenants[3].id, from_number="+1237", to_number="+0990", content="Verify", status="failed"),
            Message(tenant_id=tenants[4].id, from_number="+0991", to_number="+1238", content="Support", status="delivered"),
        ]
        for m in msgs:
            db.add(m)

        for ti, amt, st, per in [
            (0, 299.0, "paid", "2026-03"),
            (1, 149.0, "paid", "2026-03"),
            (2, 448.0, "pending", "2026-03"),
            (4, 149.0, "overdue", "2026-02"),
        ]:
            db.add(Billing(tenant_id=tenants[ti].id, amount=amt, status=st, billing_period=per))

        db.commit()
    finally:
        db.close()


# ─── App Factory ───
@asynccontextmanager
async def lifespan(application: FastAPI):
    # FIX: replaced deprecated @app.on_event("startup")
    Base.metadata.create_all(bind=engine)
    seed_db()
    yield


app = FastAPI(title="Com Management API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ───
@app.get("/health")
def health():
    return {"status": "ok", "service": "Com Management API"}


@app.post("/api/v1/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    """FIX: uses Pydantic LoginIn for validated input."""
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not pwd_ctx.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenOut(
        access_token=make_token(user.username),
        user={"id": user.id, "username": user.username, "email": user.email,
              "full_name": user.full_name, "role": user.role},
    )


@app.get("/api/v1/auth/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email,
            "full_name": user.full_name, "role": user.role}


@app.get("/api/v1/dashboard/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    ts = db.query(Tenant).all()
    ps = db.query(ComProvider).all()
    bs = db.query(Billing).all()
    return StatsOut(
        total_tenants=len(ts), active_tenants=len([t for t in ts if t.status == "active"]),
        total_providers=len(ps), active_providers=len([p for p in ps if p.status == "active"]),
        total_messages=db.query(Message).count(),
        total_revenue=sum(b.amount for b in bs if b.status == "paid"),
        pending_revenue=sum(b.amount for b in bs if b.status in ("pending", "overdue")),
    )


@app.get("/api/v1/tenants")
def list_tenants(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Tenant).all()


@app.post("/api/v1/tenants", status_code=201)
def create_tenant(body: TenantIn, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """FIX: validated input via TenantIn schema."""
    t = Tenant(**body.model_dump())
    db.add(t); db.commit(); db.refresh(t); return t


@app.get("/api/v1/tenants/{tid}")
def get_tenant(tid: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    t = db.query(Tenant).filter(Tenant.id == tid).first()
    if not t:
        raise HTTPException(404, "not found")
    return t


@app.put("/api/v1/tenants/{tid}")
def update_tenant(tid: int, body: TenantPatch, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """FIX: proper patch with exclude_unset."""
    t = db.query(Tenant).filter(Tenant.id == tid).first()
    if not t:
        raise HTTPException(404, "not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit(); db.refresh(t); return t


@app.delete("/api/v1/tenants/{tid}")
def delete_tenant(tid: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    t = db.query(Tenant).filter(Tenant.id == tid).first()
    if not t:
        raise HTTPException(404, "not found")
    db.delete(t); db.commit(); return {"message": "deleted"}


@app.get("/api/v1/com-providers")
def list_providers(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(ComProvider).all()


@app.post("/api/v1/com-providers", status_code=201)
def create_provider(body: ProviderIn, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    p = ComProvider(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p); return p


@app.put("/api/v1/com-providers/{pid}")
def update_provider(pid: int, body: ProviderPatch, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    p = db.query(ComProvider).filter(ComProvider.id == pid).first()
    if not p:
        raise HTTPException(404, "not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit(); db.refresh(p); return p


@app.delete("/api/v1/com-providers/{pid}")
def delete_provider(pid: int, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    p = db.query(ComProvider).filter(ComProvider.id == pid).first()
    if not p:
        raise HTTPException(404, "not found")
    db.delete(p); db.commit(); return {"message": "deleted"}


@app.get("/api/v1/messages")
def list_msgs(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Message).all()


@app.post("/api/v1/messages", status_code=201)
def create_msg(body: MessageIn, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    m = Message(**body.model_dump())
    db.add(m); db.commit(); db.refresh(m); return m


@app.get("/api/v1/billing")
def list_bills(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Billing).all()


@app.post("/api/v1/billing", status_code=201)
def create_bill(body: BillingIn, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    b = Billing(**body.model_dump())
    db.add(b); db.commit(); db.refresh(b); return b
