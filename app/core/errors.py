from fastapi import HTTPException, status


def unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                         detail="Unauthorized")


def backend_not_found(name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, 
                         detail=f"Backend not found: {name}")


def backend_unavailable(name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, 
                         detail=f"Backend '{name}' is unavailable")


def backend_overloaded(name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
        detail=f"Backend '{name}' is temporarily unavailable (circuit open)",
    )


def invalid_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                         detail=message)


def too_many_requests(retry_after: float) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Rate limit exceeded",
        headers={"Retry-After": str(int(retry_after) + 1)},
    )


def scheduler_saturated() -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is at capacity, try again later")