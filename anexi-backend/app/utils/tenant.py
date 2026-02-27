from fastapi import HTTPException, status


def require_tenant_id(value: int | None) -> int:
    tenant_id = int(value or 0)
    if tenant_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context is missing",
        )
    return tenant_id
