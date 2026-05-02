from models.user import RegistrationModel, CreatePostModel, BaseThreadModel, BaseChatModel, BaseMessageModel, BaseCommentModel
from datetime import datetime
from core import passwords
import uuid
from pathlib import Path
import os

import requests
# from imgurpython import ImgurClient


client_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
client_secret = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
access_token = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
refresh_token = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"


def get_file_extension(path):
    return os.path.splitext(path)[1].lower()

def upload_file(path):
    extension = get_file_extension(path)
    headers = {'Authorization': f'Bearer {access_token}'}

    with open(path, 'rb') as f:
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.apng', '.tiff']:
            response = requests.post(
                'https://api.imgur.com/3/upload',
                headers=headers,
                files={'image': f}
            )

        elif extension in ['.mp4', '.mov']:
            response = requests.post(
                'https://api.imgur.com/3/upload',
                headers=headers,
                files={'video': f}
            )

        else:
            print("❌ Неподдерживаемый формат:", extension)
            return

    if response.status_code == 200:
        data = response.json()['data']
        print("✅ Успешно загружено!")
        return data.get('link') or data.get('mp4')
    
    else:
        print("❌ Ошибка загрузки:", response.status_code)
        print(response.json())




def create_user(username: str, unhashed_password: str, birthday: str, sex: str):
    
    birthday_split = birthday.split("-")
    return RegistrationModel(

        user_id=str(uuid.uuid4()),
        username=username,
        birthday=datetime(int(birthday_split[0]), int(birthday_split[1]), int(birthday_split[2])).strftime("%d/%m/%y"),
        register_date=datetime.now().strftime("%d/%m/%y %H:%M"),
        password=passwords.hash_password(unhashed_password),
        achievements=[],
        last_time_active=datetime.now().strftime("%d/%m/%y %H:%M"),
        sex=sex,
        avatar="",
        banner="",
        description="",
        status="Online"
    )


def authenticate(auth_data, row):

    if row is None:
                # raise AuthError("User does not exist")
                raise TypeError("User does not exist")

    password_hashed = row[0]

    if not passwords.passwords_equal(auth_data.password, password_hashed):
        # raise AuthError("Password is incorrect")
        raise TypeError("Password is incorrect")

    assert auth_data.username is not None



def upload_image(data):
    image_uploaded = upload_file(path=data.picture)

    return CreatePostModel(
         
        id=str(uuid.uuid4()),
        title=data.title,
        desc=data.desc,
        picture=image_uploaded,
        likes=0,
        comms=0,
        author_id=data.author_id,
        date_created=datetime.now().strftime("%d/%m/%y %H:%M"),
        file_extension=data.file_extension,
        location_id=data.location_id,
        author_str=data.author_str,
        location_str=data.location_str,

    )



def upload_avatar(avatar_path):
    avatar_uploaded = upload_file(path=avatar_path)
    return avatar_uploaded


def upload_banner(banner_path):
    banner_uploaded = upload_file(path=banner_path) 
    return banner_uploaded



def create_thread(data):
    avatar_uploaded = upload_file(path=data.avatar)
    banner_uploaded = upload_file(path=data.banner) 


    return BaseThreadModel(
         
        id=str(uuid.uuid4()),
        name=data.name,
        desc=data.desc,
        avatar=avatar_uploaded,
        banner=banner_uploaded,
        members=0,
        posts=0,
        admin=data.admin,
        date_created=datetime.now().strftime("%d/%m/%y %H:%M"),
        tag="@" + data.tag

    )


def create_message(data):
    if data.picture == "" and data.file_extension == "":
         
        return BaseMessageModel(
        
            id=str(uuid.uuid4()),
            chat_id=data.chat_id,
            text=data.text,
            picture=data.picture,
            author_id=data.author_id,
            author_str=data.author_str,
            file_extension=data.file_extension

        )

    else:
        picture_uploaded = upload_file(path=data.picture)

            
        return BaseMessageModel(
            
            id=str(uuid.uuid4()),
            chat_id=data.chat_id,
            text=data.text,
            picture=picture_uploaded,
            author_id=data.author_id,
            author_str=data.author_str,
            date_created=datetime.now().strftime("%d/%m/%y %H:%M"),
            file_extension=data.file_extension

        )




def create_comment(data):
        
        return BaseCommentModel(
        
            id=str(uuid.uuid4()),
            text=data.text,
            date_created=datetime.now().strftime("%d/%m/%y %H:%M"),
            author_id=data.author_id,
            author_str=data.author_str,
            location_id=data.location_id,
            location_str=data.location_str,
            likes=0

        )
