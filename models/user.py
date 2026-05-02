from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any

class RegistrationModel(BaseModel):
    user_id: str
    username: str = Field(min_length=4)
    birthday: str
    register_date: str
    password: str = Field(min_length=8)
    achievements: list
    last_time_active: str
    sex: str
    avatar: str
    banner: str
    description: str
    status: str


    @field_validator("username")
    def validate_username(cls, username: str) -> str:
        assert " " not in username, "No spaces allowed in username"
        return username
    
    @field_validator("password")
    def validate_password(cls, password: str) -> str:
        assert " " not in password, "No spaces allowed in password"
        return password


class BaseUserModel(BaseModel):
    id: str
    username: str
    birthday: str
    register_date: str
    achievements: list
    last_time_active: str
    sex: str
    avatar: str
    banner: str
    description: str
    status: str


class AdModel(BaseModel):
    title: str
    text: str

class UserModel(BaseModel):
    id: str
    username: str
    

class AuthUserModel(BaseModel):
    username: str
    password: str

class CookieModel(BaseModel):
    id: str
    user_id: str
    expires: float

class CreatePostModel(BaseModel):
    id: str
    title: str
    desc: str
    picture: Any
    likes: int
    comms: int
    author_id: str
    date_created: str
    file_extension: str
    location_id: str
    author_str: str
    location_str: str


class UploadPostModel(BaseModel):
    title: str
    desc: str
    picture: str
    author_id: str
    file_extension: str
    location_id: str
    author_str: str
    location_str: str


class SearchAnswerModel(BaseModel):
    users: list | None
    posts: list | None
    threads: list | None
    

class BaseNotifModel(BaseModel):
    id: str
    user_id: str
    text: str
    datetime: str
    read: bool


class LikeRequest(BaseModel):
    post_id: str


class BasePostModel(BaseModel):
    id: str
    title: str
    desc: str
    picture: Any
    likes: int
    comms: int
    author_id: str
    date_created: str
    file_extension: str
    location_id: str
    author_str: str
    location_str: str
    avatar: str
    liked_by_user: Optional[Any] = None




class SearchResultModel(BaseModel):
    search_type: str
    id: str
    name: str
    desc: str
    avatar: str
    location_status: str


class BaseThreadModel(BaseModel):
    id: str
    name: str
    desc: str
    avatar: Any
    banner: Any
    members: int
    posts: int
    admin: str
    date_created: str
    tag: str

class ShowThreadTag(BaseModel):
    id: str
    tag: str

class UploadThreadModel(BaseModel):
    name: str
    desc: str
    avatar: str
    banner: str
    admin: str
    tag: str

class BaseFollowModel(BaseModel):
    id: str
    follows: str
    follow_type: Optional[str]

class BaseChatModel(BaseModel):
    id: str
    user1_id: str
    user1_str: str
    user2_id: str
    user2_str: str


class BaseMessageModel(BaseModel):
    id: str
    chat_id: str
    text: str
    picture: str
    author_id: str
    author_str: str
    date_created: Optional[Any] = None
    date_time_created: Optional[Any] = None
    file_extension: str


class BaseCommentModel(BaseModel):
    id: str
    text: str
    date_created: str
    author_id: str
    author_str: str
    location_id: str
    location_str: str
    likes: int
    avatar: Optional[str] = None


class UploadCommentModel(BaseModel):
    text: str
    author_id: str
    author_str: str
    location_id: str
    location_str: str


class UploadMessageModel(BaseModel):
    chat_id: str
    text: str
    picture: Any
    author_id: str
    author_str: str
    file_extension: str
    

class LeaderboardValueModel(BaseModel):
    username: str
    value: Any
    avatar: str

class LeaderboardValueListModel(BaseModel):
    friends: list
    posts: list
    hours: list


    

    