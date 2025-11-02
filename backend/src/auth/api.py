from .crud import authenticate_user, update_user_profile
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(login_data: LoginRequest):
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        user = await authenticate_user(login_data.email, login_data.password)
        if not user:
            logger.warning(f"Failed login attempt for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неправильный email или пароль"
            )
        
        # Create access token with user email
        access_token = create_access_token(data={"sub": user["email"]})
        logger.info(f"Successful login for email: {login_data.email}")
        
        try:
            user_info = {
                "id": str(user.get("id") or user.get("_id", "")),
                "name": user.get("name", ""),
                "email": user.get("email", "")
            }
            
            user_response = {
                "token": access_token, 
                "token_type": "bearer",
                "user": user_info,
                "message": "Login successful"
            }
            
            logger.debug(f"Login response: {user_response}")
            return user_response
        except Exception as e:
            logger.error(f"Error creating user response: {e}")
            # Return minimal response if user serialization fails
            return {
                "access_token": access_token, 
                "token_type": "bearer"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )



