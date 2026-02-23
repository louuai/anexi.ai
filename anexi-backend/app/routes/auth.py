import json
import logging
import os
import secrets
import urllib.parse
import urllib.request

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models import User, UserProfile
from app.schemas import (
    SignupRequest,
    ProfileRequest,
    LoginRequest,
    TokenResponse,
    ProfileSettingsResponse,
    ProfileSettingsUpdateRequest,
    ProfilePasswordUpdateRequest,
    NotificationSettings,
    SystemSettings,
)
from app.utils.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


def _normalize_role(role: str | None) -> str:
    return str(role or "user").strip().lower()


def _build_frontend_redirect_url(path: str = "/login.html") -> str:
    base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{base}{normalized_path}"


def _google_oauth_config() -> tuple[str, str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback").strip()

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google auth is not configured on the server (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET)."
        )

    return client_id, client_secret, redirect_uri


@router.post("/signup", response_model=dict)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    """
    Créer un nouveau compte utilisateur
    """
    # Check if email already exists
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà enregistré"
        )

    # Hash password before storing
    hashed_pwd = hash_password(data.password)
    
    user = User(
        email=data.email,
        password_hash=hashed_pwd,
        full_name=data.full_name,
        role=data.role or "user",
    )
    
    db.add(user)
    
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà enregistré"
        )

    return {
        "message": "Compte créé avec succès",
        "user_id": user.id,
        "email": user.email
    }


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Connexion utilisateur avec JWT token
    """
    # Find user by email
    user = db.query(User).filter_by(email=data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": _normalize_role(user.role)}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id
    )


@router.post("/profile", response_model=dict)
def choose_profile(data: ProfileRequest, db: Session = Depends(get_db)):
    """
    Choisir le profil de vente du merchant
    """
    user = db.get(User, data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Check if profile already exists
    existing_profile = db.query(UserProfile).filter_by(user_id=user.id).first()
    
    if existing_profile:
        # Update existing profile
        existing_profile.selling_type = data.selling_type
        db.commit()
        db.refresh(existing_profile)
        return {
            "message": "Profil mis à jour",
            "profile_id": existing_profile.id
        }
    
    # Create new profile
    profile = UserProfile(user_id=user.id, selling_type=data.selling_type)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {
        "message": "Profil enregistré",
        "profile_id": profile.id
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency pour récupérer l'utilisateur authentifié
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Récupérer les informations de l'utilisateur connecté
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "role": _normalize_role(current_user.role),
        "created_at": current_user.created_at
    }


def _ensure_user_profile(db: Session, user_id: int) -> UserProfile:
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    if profile:
        return profile

    profile = UserProfile(user_id=user_id, selling_type="mix")
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile/settings", response_model=ProfileSettingsResponse)
def get_profile_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _ensure_user_profile(db, current_user.id)
    return ProfileSettingsResponse(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        notifications=NotificationSettings(
            order_updates=bool(profile.notifications_order_updates),
            risk_alerts=bool(profile.notifications_risk_alerts),
            email_digest=bool(profile.notifications_email_digest),
        ),
        system=SystemSettings(
            language=profile.system_language or "en",
            timezone=profile.system_timezone or "UTC",
        ),
    )


@router.put("/profile/settings", response_model=ProfileSettingsResponse)
def update_profile_settings(
    payload: ProfileSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = _ensure_user_profile(db, current_user.id)

    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() or None
    if payload.email is not None:
        current_user.email = payload.email.lower().strip()
    if payload.phone is not None:
        current_user.phone = payload.phone.strip() or None
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url.strip() or None

    if payload.notifications is not None:
        profile.notifications_order_updates = bool(payload.notifications.order_updates)
        profile.notifications_risk_alerts = bool(payload.notifications.risk_alerts)
        profile.notifications_email_digest = bool(payload.notifications.email_digest)

    if payload.system is not None:
        profile.system_language = (payload.system.language or "en").strip()[:10]
        profile.system_timezone = (payload.system.timezone or "UTC").strip()[:64]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà enregistré",
        )

    db.refresh(current_user)
    db.refresh(profile)

    return ProfileSettingsResponse(
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        notifications=NotificationSettings(
            order_updates=bool(profile.notifications_order_updates),
            risk_alerts=bool(profile.notifications_risk_alerts),
            email_digest=bool(profile.notifications_email_digest),
        ),
        system=SystemSettings(
            language=profile.system_language or "en",
            timezone=profile.system_timezone or "UTC",
        ),
    )


@router.put("/profile/password", response_model=dict)
def update_profile_password(
    payload: ProfilePasswordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.new_password or len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit contenir au moins 8 caractères",
        )

    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit être différent de l'actuel",
        )

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour"}


@router.get("/google/login")
def google_login():
    """
    Redirect user to Google's OAuth consent screen.
    """
    frontend_login = _build_frontend_redirect_url("/login.html")
    try:
        client_id, _, redirect_uri = _google_oauth_config()
    except HTTPException as exc:
        error = urllib.parse.quote(str(exc.detail))
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

    state = secrets.token_urlsafe(24)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state,
    }

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
def google_callback(code: str = Query(default=""), state: str = Query(default=""), db: Session = Depends(get_db)):
    """
    OAuth callback: exchange code for token, fetch profile, create/login user, then redirect to frontend.
    """
    del state  # state is currently not persisted server-side

    frontend_login = _build_frontend_redirect_url("/login.html")

    if not code:
        error = urllib.parse.quote("Google OAuth failed: missing authorization code.")
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

    try:
        client_id, client_secret, redirect_uri = _google_oauth_config()
    except HTTPException as exc:
        error = urllib.parse.quote(str(exc.detail))
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

    token_payload = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")

    token_request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(token_request, timeout=10) as token_response:
            token_data = json.loads(token_response.read().decode("utf-8"))
    except Exception:
        error = urllib.parse.quote("Could not exchange Google auth code for access token.")
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

    access_token = token_data.get("access_token")
    if not access_token:
        error = urllib.parse.quote("Google access token is missing in token response.")
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

    userinfo_request = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    try:
        with urllib.request.urlopen(userinfo_request, timeout=10) as userinfo_response:
            google_user = json.loads(userinfo_response.read().decode("utf-8"))
    except Exception:
        error = urllib.parse.quote("Could not fetch Google profile information.")
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

    email = (google_user.get("email") or "").strip().lower()
    full_name = (google_user.get("name") or "Google User").strip()[:100]

    if not email:
        error = urllib.parse.quote("Google account email is missing.")
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

    try:
        is_new_user = False
        user_row = db.execute(
            text("SELECT id, email, role FROM users WHERE email = :email LIMIT 1"),
            {"email": email[:100]},
        ).mappings().first()

        if not user_row:
            random_pwd = secrets.token_urlsafe(32)
            try:
                db.execute(
                    text(
                        """
                        INSERT INTO users (full_name, email, password_hash, role)
                        VALUES (:full_name, :email, :password_hash, :role)
                        """
                    ),
                    {
                        "full_name": full_name,
                        "email": email[:100],
                        "password_hash": hash_password(random_pwd),
                        "role": "user",
                    },
                )
                db.commit()
                is_new_user = True
            except IntegrityError:
                db.rollback()
            except Exception:
                db.rollback()
                raise

            user_row = db.execute(
                text("SELECT id, email, role FROM users WHERE email = :email LIMIT 1"),
                {"email": email[:100]},
            ).mappings().first()

        if not user_row:
            error = urllib.parse.quote("Could not create or retrieve user account.")
            return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")

        app_token = create_access_token(
            data={
                "sub": user_row["email"],
                "user_id": int(user_row["id"]),
                "role": _normalize_role(user_row["role"]),
            }
        )
        query = urllib.parse.urlencode(
            {
                "token": app_token,
                "user_id": int(user_row["id"]),
                "first_login": "1" if is_new_user else "0",
            }
        )
        return RedirectResponse(url=f"{frontend_login}?{query}")
    except Exception as exc:
        logger.exception("Google callback failed during DB/token stage")
        # Never surface a raw 500 page during OAuth redirects
        error = urllib.parse.quote(
            f"Server database error during Google sign-in ({exc.__class__.__name__})."
        )
        return RedirectResponse(url=f"{frontend_login}?oauth_error={error}")
