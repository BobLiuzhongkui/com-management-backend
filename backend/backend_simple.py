"""
Backend: FastAPI + SQLite (port 8001)
Matches the cloned frontend's API contract: /api/v1/* routes
"""
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, relationship
from pydantic import BaseModel, ConfigDict
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, List

# ─── Database ───
engine = create_engine("sqlite:///./com.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="admin")

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text); contact_email = Column(String(100)); contact_phone = Column(String(20))
    status = Column(String(20), default="active")

class ComProvider(Base):
    __tablename__ = "com_providers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(String(30), default="SMS"); api_endpoint = Column(String(500))
    status = Column(String(20), default="active")
    monthly_cost = Column(Float, default=0)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer); from_number = Column(String(50)); to_number = Column(String(50))
    content = Column(Text); direction = Column(String(10), default="outbound")
    status = Column(String(20), default="sent")

class Billing(Base):
    __tablename__ = "billings"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer); amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    billing_period = Column(String(20)); description = Column(Text)

Base.metadata.create_all(bind=engine)

# ─── Schemas ───
class Token(BaseModel): access_token: str; token_type: str = "bearer"; user: dict
class UserResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; username: str; email: Optional[str] = None
    full_name: Optional[str] = None; role: str

class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; description: Optional[str] = None
    contact_email: Optional[str] = None; contact_phone: Optional[str] = None
    status: str

class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; name: str; provider_type: str; api_endpoint: Optional[str] = None
    status: str; monthly_cost: float; created_at: Optional[datetime] = None

class MsgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; tenant_id: Optional[int] = None; from_number: Optional[str] = None
    to_number: Optional[str] = None; content: Optional[str] = None
    direction: str; status: str

class BillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int; tenant_id: Optional[int] = None; amount: float; status: str
    billing_period: Optional[str] = None; description: Optional[str] = None

class StatsResp(BaseModel):
    total_tenants: int = 0; active_tenants: int = 0
    total_providers: int = 0; active_providers: int = 0
    total_messages: int = 0; total_revenue: float = 0
    pending_revenue: float = 0

class LoginIn(BaseModel): username: str; password: str

# ─── App ───
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SECRET = "dev-key-2026"; ALGO = "HS256"
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
get_db = lambda: Session()

def seed():
    s = Session()
    if s.query(User).first(): s.close(); return
    s.add(User(username="admin", email="admin@example.com", hashed_password=pwd.hash("admin123"), full_name="Admin"))
    s.flush()
    for n, d, e, st in [("Acme Corp","Primary","admin@acme.com","active"),("TechStart Inc","Startup","info@tech.io","active"),
        ("Global Media","Media","contact@gm.com","active"),("CloudNet","Cloud","support@cn.io","suspended"),("SmartBiz","Smart","hello@sb.com","active")]:
        s.add(Tenant(name=n, description=d, contact_email=e, status=st))
    s.flush()
    ts = s.query(Tenant).all()
    for n, pt, ep, c, st in [("Twilio SMS","SMS","https://api.twilio.com",299.0,"active"),
        ("SendGrid","Email","https://api.sendgrid.com",149.0,"active"),
        ("Vonage","Voice","https://rest.nexmo.com",199.0,"active"),
        ("SIP Trunk","VoIP","sip:example.com",499.0,"maintenance")]:
        s.add(ComProvider(name=n, provider_type=pt, api_endpoint=ep, monthly_cost=c, status=st))
    for ti, fr, to, c, st in [(0,"+1234","+0987","Welcome","delivered"),(0,"+0987","+1234","Thanks","delivered"),
        (1,"+1235","+0988","Order #123","delivered"),(2,"+1236","+0989","Alert","sent"),
        (3,"+1237","+0990","Verify","failed"),(4,"+0991","+1238","Support","delivered")]:
        s.add(Message(tenant_id=ts[ti].id, from_number=fr, to_number=to, content=c, status=st))
    for ti, amt, st, per in [(0,299.0,"paid","2026-03"),(1,149.0,"paid","2026-03"),(2,448.0,"pending","2026-03"),(4,149.0,"overdue","2026-02")]:
        s.add(Billing(tenant_id=ts[ti].id, amount=amt, status=st, billing_period=per))
    s.commit(); s.close()

def token(data):
    d = data.copy(); d["exp"] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(d, SECRET, algorithm=ALGO)

def get_u(t=Depends(oauth), s=Depends(get_db)):
    sub = jwt.decode(t, SECRET, algorithms=[ALGO]).get("sub") if t else None
    user = s.query(User).filter(User.username == sub).first() if sub else None
    if not user: raise HTTPException(401, "bad")
    return user

@app.on_event("startup")
def _seed(): seed()

@app.get("/health")
def health(): return {"status":"ok","service":"Com Management API"}

@app.post("/api/v1/auth/login", response_model=Token)
def login(r: LoginIn, s=Depends(get_db)):
    u = s.query(User).filter(User.username == r.username).first()
    if not u or not pwd.verify(r.password, u.hashed_password): raise HTTPException(401, "invalid")
    return Token(access_token=token({"sub": u.username}), user=UserResp(id=u.id, username=u.username, email=u.email, full_name=u.full_name, role=u.role).model_dump())

@app.get("/api/v1/auth/me")
def me(u=Depends(get_u)): return {"id":u.id,"username":u.username,"email":u.email,"full_name":u.full_name,"role":u.role}

@app.get("/api/v1/dashboard/stats", response_model=StatsResp)
def stats(s=Depends(get_db), _u=Depends(get_u)):
    ts = s.query(Tenant).all()
    return StatsResp(total_tenants=len(ts), active_tenants=len([t for t in ts if t.status=="active"]),
        total_providers=s.query(ComProvider).count(), active_providers=s.query(ComProvider).filter(ComProvider.status=="active").count(),
        total_messages=s.query(Message).count(),
        total_revenue=sum(b.amount for b in s.query(Billing).filter(Billing.status=="paid").all()),
        pending_revenue=sum(b.amount for b in s.query(Billing).filter(Billing.status.in_(["pending","overdue"])).all()))

@app.get("/api/v1/tenants", response_model=List[TenantOut])
def list_tenants(s=Depends(get_db)): return s.query(Tenant).all()

@app.get("/api/v1/tenants/{tid}", response_model=TenantOut)
def get_tenant(tid: int, s=Depends(get_db)):
    t = s.query(Tenant).filter(Tenant.id==tid).first()
    if not t: raise HTTPException(404,"not found")
    return t

@app.post("/api/v1/tenants", response_model=TenantOut)
def create_tenant(data: dict, s=Depends(get_db)): t = Tenant(**data); s.add(t); s.commit(); s.refresh(t); return t

@app.put("/api/v1/tenants/{tid}", response_model=TenantOut)
def update_tenant(tid: int, data: dict, s=Depends(get_db)):
    t = s.query(Tenant).filter(Tenant.id==tid).first()
    if not t: raise HTTPException(404,"not found")
    for k,v in data.items(): setattr(t,k,v)
    s.commit(); s.refresh(t); return t

@app.delete("/api/v1/tenants/{tid}")
def delete_tenant(tid: int, s=Depends(get_db)):
    t = s.query(Tenant).filter(Tenant.id==tid).first()
    if not t: raise HTTPException(404,"not found")
    s.delete(t); s.commit(); return {"message":"deleted"}

@app.get("/api/v1/com-providers", response_model=List[ProviderOut])
def list_providers(s=Depends(get_db)): return s.query(ComProvider).all()

@app.post("/api/v1/com-providers", response_model=ProviderOut)
def create_provider(data: dict, s=Depends(get_db)): p = ComProvider(**data); s.add(p); s.commit(); s.refresh(p); return p

@app.put("/api/v1/com-providers/{pid}", response_model=ProviderOut)
def update_provider(pid: int, data: dict, s=Depends(get_db)):
    p = s.query(ComProvider).filter(ComProvider.id==pid).first()
    if not p: raise HTTPException(404,"not found")
    for k,v in data.items(): setattr(p,k,v)
    s.commit(); s.refresh(p); return p

@app.delete("/api/v1/com-providers/{pid}")
def delete_provider(pid: int, s=Depends(get_db)):
    p = s.query(ComProvider).filter(ComProvider.id==pid).first()
    if not p: raise HTTPException(404,"not found")
    s.delete(p); s.commit(); return {"message":"deleted"}

@app.get("/api/v1/messages", response_model=List[MsgOut])
def list_msgs(s=Depends(get_db)): return s.query(Message).all()

@app.post("/api/v1/messages", response_model=MsgOut)
def create_msg(data: dict, s=Depends(get_db)): m = Message(**data); s.add(m); s.commit(); s.refresh(m); return m

@app.get("/api/v1/billing", response_model=List[BillOut])
def list_bills(s=Depends(get_db)): return s.query(Billing).all()

@app.post("/api/v1/billing", response_model=BillOut)
def create_bill(data: dict, s=Depends(get_db)): b = Billing(**data); s.add(b); s.commit(); s.refresh(b); return b
