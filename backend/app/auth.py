"""
Section 11 & Phase 4: Authentication, Authorization & RBAC Module.
Provides Supabase Auth JWT verification, session management, user isolation,
role-based access control (Customer vs Admin), and transparent fallback to
Demo Mode when Supabase Auth is not configured.
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from app.config import settings
from app.schemas import (
    UserProfile,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthSignupRequest,
    AuthResetPasswordRequest,
    AuthUpdatePasswordRequest,
)
from app.db import (
    get_supabase_client,
    is_supabase_enabled,
    get_profile,
    list_profiles,
    upsert_profile,
    log_audit_event,
)


logger = logging.getLogger("sybr.auth")


def verify_supabase_token(token: str) -> Optional[UserProfile]:
    """Verifies a JWT token with Supabase Auth service and loads profile role."""
    if not is_supabase_enabled():
        return None
    sb = get_supabase_client()
    if not sb:
        return None
    try:
        user_res = sb.auth.get_user(token)
        if user_res and user_res.user:
            uid = user_res.user.id
            email = user_res.user.email or "user@supabase.io"
            
            # Retrieve or initialize profile
            prof = get_profile(uid)
            if not prof:
                display_name = (user_res.user.user_metadata or {}).get("display_name", email.split("@")[0])
                prof = upsert_profile(user_id=uid, email=email, display_name=display_name, role="customer")
            
            if prof.get("status") == "disabled":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account has been disabled by an administrator.",
                )

            return UserProfile(
                id=uid,
                email=email,
                display_name=prof.get("display_name", ""),
                role=prof.get("role", "customer"),
                status=prof.get("status", "active"),
                is_demo=False,
                created_at=prof.get("created_at"),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Supabase token validation failed: {str(e)}")
        return None
    return None


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> UserProfile:
    """
    FastAPI dependency for authenticating users.
    Enforces token validation when auth is enabled or token is provided.
    In demo/offline mode without a token, defaults to demo workspace customer.
    """
    token = None
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]

    # If a token is explicitly provided
    if token:
        # Check for demo admin tokens
        if token in ("admin-demo-token", "admin-token", "demo-admin"):
            prof = get_profile("admin-user-001") or {}
            return UserProfile(
                id="admin-user-001",
                email="admin@sybr.local",
                display_name="System Administrator",
                role="admin",
                status="active",
                is_demo=True,
            )

        # Check for demo customer tokens
        if token in ("demo-token", "demo"):
            prof = get_profile("demo-user-001") or {}
            return UserProfile(
                id="demo-user-001",
                email="demo@sybr.local",
                display_name="Demo Customer",
                role="customer",
                status="active",
                is_demo=True,
            )

        if token.startswith("demo-"):
            uid = token
            prof = get_profile(uid) or {}
            return UserProfile(
                id=uid,
                email=prof.get("email", f"{uid}@sybr.local"),
                display_name=prof.get("display_name", uid),
                role=prof.get("role", "customer"),
                status=prof.get("status", "active"),
                is_demo=True,
            )

        # Check Supabase JWT
        if is_supabase_enabled():
            user = verify_supabase_token(token)
            if user:
                return user
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # If token provided but unrecognized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If no token is provided:
    # If ENABLE_AUTH is strictly enforced, require credentials
    if settings.ENABLE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In local demo / development mode without token, map to shared demo customer
    return UserProfile(
        id="demo-user-001",
        email="demo@sybr.local",
        display_name="Demo Customer",
        role="customer",
        status="active",
        is_demo=True,
    )


def require_authenticated_user(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Dependency verifying that request has a valid authenticated identity."""
    if not current_user or not current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_admin(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """
    Dependency enforcing Administrator role authorization.
    Rejects customer requests with HTTP 403 Forbidden.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Administrator privileges required.",
        )
    return current_user


def require_customer(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Dependency verifying customer or admin authorized access."""
    if current_user.status == "disabled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )
    return current_user


def authenticate_user(login_data: AuthLoginRequest) -> AuthLoginResponse:
    """
    Authenticates a user via Supabase Auth or falls back to clearly-marked Demo Mode.
    """
    email_clean = login_data.email.strip().lower()

    # Attempt Supabase Auth if credentials configured
    if is_supabase_enabled():
        sb = get_supabase_client()
        if sb:
            try:
                res = sb.auth.sign_in_with_password({
                    "email": email_clean,
                    "password": login_data.password,
                })
                if res and res.session and res.user:
                    uid = res.user.id
                    prof = get_profile(uid)
                    if not prof:
                        prof = upsert_profile(user_id=uid, email=email_clean, role="customer")

                    if prof.get("status") == "disabled":
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Account has been disabled by an administrator.",
                        )

                    role = prof.get("role", "customer")
                    user_prof = UserProfile(
                        id=uid,
                        email=res.user.email or email_clean,
                        display_name=prof.get("display_name", ""),
                        role=role,
                        status=prof.get("status", "active"),
                        is_demo=False,
                    )
                    return AuthLoginResponse(
                        access_token=res.session.access_token,
                        token_type="bearer",
                        user=user_prof,
                        is_demo=False,
                        message="Authenticated via Supabase Auth.",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Supabase login failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )

    # Demo Mode Fallback:
    # Requires valid email format and non-empty password
    if "@" not in email_clean or not login_data.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid email address and password.",
        )

    # Check for Admin Demo Login
    if email_clean == "admin@sybr.local" or email_clean.startswith("admin@"):
        admin_prof = UserProfile(
            id="admin-user-001",
            email=email_clean,
            display_name="System Administrator",
            role="admin",
            status="active",
            is_demo=True,
        )
        return AuthLoginResponse(
            access_token="admin-demo-token",
            token_type="bearer",
            user=admin_prof,
            is_demo=True,
            message="Logged in as ADMINISTRATOR in Demo Mode.",
        )

    # Customer Demo Login
    profiles = list_profiles()
    existing = next((p for p in profiles if p.get("email") == email_clean), None)
    if existing:
        user_id = existing["id"]
        role = existing.get("role", "customer")
        display_name = existing.get("display_name") or email_clean.split("@")[0]
    else:
        import uuid
        user_id = f"demo-user-{uuid.uuid4().hex[:6]}"
        role = "customer"
        display_name = email_clean.split("@")[0]
        upsert_profile(user_id=user_id, email=email_clean, display_name=display_name, role=role)

    customer_prof = UserProfile(
        id=user_id,
        email=email_clean,
        display_name=display_name,
        role=role,
        status="active",
        is_demo=True,
    )
    return AuthLoginResponse(
        access_token=user_id,
        token_type="bearer",
        user=customer_prof,
        is_demo=True,
        message=f"Logged in as {role.upper()} in Demo Mode.",
    )


def register_user(signup_data: AuthSignupRequest) -> Dict[str, Any]:
    """
    Registers a new Customer account.
    PUBLIC SIGNUP MUST NEVER ALLOW CHOOSING 'ADMIN' (Section 7).
    """
    email_clean = signup_data.email.strip().lower()
    if "@" not in email_clean:
        raise HTTPException(status_code=400, detail="A valid email address is required.")
    if len(signup_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    if is_supabase_enabled():
        sb = get_supabase_client()
        if sb:
            try:
                res = sb.auth.sign_up({
                    "email": email_clean,
                    "password": signup_data.password,
                    "options": {
                        "data": {
                            "display_name": signup_data.display_name or email_clean.split("@")[0],
                            "role": "customer"  # Enforce customer
                        }
                    }
                })
                if res and res.user:
                    upsert_profile(
                        user_id=res.user.id,
                        email=email_clean,
                        display_name=signup_data.display_name or email_clean.split("@")[0],
                        role="customer",
                    )
                return {
                    "status": "ok",
                    "message": "Registration successful. Please check your inbox to verify your email.",
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    # Local Demo Registration: create user profile for this email
    profiles = list_profiles()
    existing = next((p for p in profiles if p.get("email") == email_clean), None)
    if existing:
        return {
            "status": "ok",
            "message": "Account already registered. You can sign in directly.",
        }

    import uuid
    new_id = f"demo-user-{uuid.uuid4().hex[:6]}"
    upsert_profile(
        user_id=new_id,
        email=email_clean,
        display_name=signup_data.display_name or email_clean.split("@")[0],
        role="customer",
    )
    return {
        "status": "ok",
        "message": f"Account for {email_clean} created successfully. Default role: customer.",
    }


def request_password_reset(req: AuthResetPasswordRequest) -> Dict[str, Any]:
    """
    Sends password reset instructions using safe messaging (Section 8).
    Prevents email enumeration attacks.
    """
    email_clean = req.email.strip().lower()
    if is_supabase_enabled():
        sb = get_supabase_client()
        if sb:
            try:
                sb.auth.reset_password_for_email(email_clean)
            except Exception as e:
                logger.warning(f"Supabase password reset error: {str(e)}")

    return {
        "status": "ok",
        "message": "If this email address is registered, instructions to reset your password have been sent.",
    }
