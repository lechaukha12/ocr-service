from typing import Optional, List, Dict, Any
from . import models, utils, database

def get_user_by_email(email: str) -> Optional[models.UserInDBBase]:
    for user_data in database.fake_users_db.values():
        if user_data["email"] == email:
            return models.UserInDBBase(**user_data)
    return None

def get_user_by_username(username: str) -> Optional[models.UserInDBBase]:
    if username in database.fake_users_db:
        return models.UserInDBBase(**database.fake_users_db[username])
    return None

def get_user_by_id(user_id: int) -> Optional[models.UserInDBBase]:
    for user_data in database.fake_users_db.values():
        if user_data["id"] == user_id:
            return models.UserInDBBase(**user_data)
    return None

def create_user(user: models.UserCreate) -> models.UserInDBBase:
    hashed_password = utils.get_password_hash(user.password)
    user_id = database.next_user_id
    
    user_in_db_data = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "is_active": True
        # Add other fields from User model as needed, with default values
        # "full_name": None,
        # "id_number": None,
        # "date_of_birth": None,
        # "gender": None,
        # "nationality": "Việt Nam",
        # "place_of_origin": None,
        # "place_of_residence": None,
        # "date_of_issue": None,
        # "ekyc_status": "pending"
    }
    
    database.fake_users_db[user.username] = user_in_db_data
    database.next_user_id += 1
    return models.UserInDBBase(**user_in_db_data)

# Later, we will add functions to update user information,
# especially after eKYC process.
# def update_user_ekyc_info(username: str, ekyc_data: models.UserEkycUpdate) -> Optional[models.UserInDBBase]:
#     pass