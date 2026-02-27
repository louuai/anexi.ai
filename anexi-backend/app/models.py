from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text, Boolean, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    Table users: Utilisateurs de la plateforme (merchants)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    avatar_url = Column(Text, nullable=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(30), nullable=False, default="user")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    boutiques = relationship("Boutique", back_populates="owner")
    payments = relationship("Payment", back_populates="user")


class UserProfile(Base):
    """
    Table user_profiles: Profil marchand (type de vente)
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    selling_type = Column(String)  # fb_ads / boutique / whatsapp / mix
    notifications_order_updates = Column(Boolean, nullable=False, default=True)
    notifications_risk_alerts = Column(Boolean, nullable=False, default=True)
    notifications_email_digest = Column(Boolean, nullable=False, default=False)
    system_language = Column(String(10), nullable=False, default="en")
    system_timezone = Column(String(64), nullable=False, default="UTC")

    # Relationships
    user = relationship("User", back_populates="profile")


class Boutique(Base):
    """
    Table boutiques: Boutiques e-commerce connectées
    """
    __tablename__ = "boutiques"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="boutiques")
    customers = relationship("Customer", back_populates="boutique")
    orders = relationship("Order", back_populates="boutique")
    ads_insights = relationship("AdsInsight", back_populates="boutique")
    payments = relationship("Payment", back_populates="boutique")


class Customer(Base):
    """
    Table customers: Clients finaux avec trust tracking
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    full_name = Column(String(100))
    phone = Column(String(20), index=True)
    email = Column(String(100))
    boutique_id = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    boutique = relationship("Boutique", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")


class Order(Base):
    """
    Table orders: Commandes clients
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    boutique_id = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    product_name = Column(String(100))
    price = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), default="pending")  # pending / confirmed / rejected / delivered
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    boutique = relationship("Boutique", back_populates="orders")
    calls = relationship("Call", back_populates="order")


class Call(Base):
    """
    Table calls: Appels de confirmation AI
    """
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    agent_id = Column(Integer)  # Future: AI agent identifier
    audio_url = Column(Text)
    transcript = Column(Text)
    ai_score = Column(Numeric(5, 2))  # Score de confiance de l'AI
    ai_decision = Column(String(30))  # confirm / reject / escalate
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    order = relationship("Order", back_populates="calls")


class AIDecision(Base):
    """
    Table ai_decisions: Décisions automatiques de l'AI Brain
    """
    __tablename__ = "ai_decisions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    source_type = Column(String(20))  # order / call / behavior
    source_id = Column(Integer, nullable=False)
    score = Column(Numeric(5, 2), nullable=False)  # Trust/risk score
    decision = Column(String(30), nullable=False)  # auto_confirm / call_required / reject
    explanation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # No direct ORM relationship to Order because source_type/source_id is polymorphic
    # and source_id is not a foreign key constrained to orders.id.


class AdsInsight(Base):
    """
    Table ads_insights: Insights des campagnes publicitaires (Facebook Ads)
    """
    __tablename__ = "ads_insights"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    boutique_id = Column(Integer, ForeignKey("boutiques.id"), nullable=False)
    source = Column(String(20))  # facebook / google / tiktok
    insight = Column(Text)
    suggestion = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    boutique = relationship("Boutique", back_populates="ads_insights")


class Payment(Base):
    """
    Table payments: Paiements/abonnements liés au marchand et à sa boutique/customer.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    boutique_id = Column(Integer, ForeignKey("boutiques.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    plan = Column(String(30), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(30), default="card")
    status = Column(String(20), default="confirmed")
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="payments")
    boutique = relationship("Boutique", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
