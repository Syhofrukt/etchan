from typing import Union, Annotated, List, Optional
from fastapi import FastAPI, Request, Form, status, Depends, HTTPException, Cookie, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from omi_project.crud import database_controller
from core.db import get_connection, open_pool, close_pool
from models.user import RegistrationModel, AuthUserModel, UploadPostModel, UploadThreadModel, BaseFollowModel, UploadMessageModel, UploadCommentModel, AdModel, BaseNotifModel, SearchResultModel, LikeRequest
from crud import create_user
from http.cookies import SimpleCookie
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import uvicorn
from typing import Any

from contextlib import asynccontextmanager

import asyncio

import threading
from time import sleep
import os

from datetime import datetime
import random

# uvicorn main:app --reload

user_crud = database_controller.UserCRUD()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_pool()

    task = asyncio.create_task(update_leaderboard())

    yield 

    task.cancel()
    await close_pool()


app = FastAPI(lifespan=lifespan)

app.add_middleware(ProxyHeadersMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


session_times = {}

@app.websocket("/ws/time")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()


    cookie_header = websocket.headers.get("cookie")
    user_id = None

    if cookie_header:
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        if "Authorization" in cookies:
            user_id = cookies["Authorization"].value

    if not user_id:
        await websocket.close(code=4401)
        return

    # Отмечаем начало сессии
    session_times[user_id] = datetime.now()

    async with get_connection() as conn:
        await user_crud.set_user_status(conn=conn, user_id=user_id, status="Online")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        start_time = session_times.pop(user_id, None)
        if not start_time:
            return

        duration = round((datetime.now() - start_time).total_seconds())


        async with get_connection() as conn:
            await user_crud.write_user_time(conn=conn, user_id=user_id, duration=duration)
            await user_crud.set_user_status(conn=conn, user_id=user_id, status="Offline")




@app.websocket("/ws/search")
async def websocket_search(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Search WebSocket received: {data}")
            # Просто уведомляем клиента, что нужно перерендерить
            await websocket.send_text("search_complete")

    except WebSocketDisconnect:
        print("WebSocket disconnected")




@app.websocket("/ws/chat")
async def websocket_endpvoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def get_auth_user(request: Request):
    
    """
    Verify that user has valid session
    
    """

    session_id = request.cookies.get("Authorization")

    if session_id is None:    
        raise HTTPException(status_code=401)
        
        
    return True

async def update_leaderboard():
    async with get_connection() as conn:
        await user_crud.leaderboard_update_values(conn=conn)
        print("leaderboard updated")
        await asyncio.sleep(600)



ads = [

    AdModel(title="GlowCharge — Power in Your Pocket",
            text="""
                Say goodbye to bulky power banks and dead phones. GlowCharge is the ultra-slim, neon-lit battery pack designed for modern life. It's the size of a credit card, fast-charges your phone twice, and glows in the dark so you’ll never lose it in your bag or at night.\n
                Perfect for festivals, travel, or just a busy day in the city.\n
                ✨ Smart. Stylish. Always ready.\n
                👉 Get yours today and light up your charge.\n
                """),
    
    AdModel(title="Plantflix — Grow What You Watch",
            text="""
                Tired of mindless streaming? Welcome to Plantflix — the world’s first interactive platform where you watch plants grow in real time.\n
                Explore livestreams from exotic greenhouses, vote on what plants get watered, join daily tutorials, and even sync your home garden with expert guidance.\n
                It’s like Netflix, but your plants thrive with every episode.\n
                🌱 Grow smarter. Chill greener. Only on Plantflix.\n
                """),

    AdModel(title="MindSprint — Microlearning for Busy Brains",
            text="""
                Got 5 minutes? That’s all you need.\n
                MindSprint is a microlearning app powered by AI that fits education into your schedule. Choose from over 100 topics — from neuroscience to UX design — and get daily 5-minute sessions tailored to your interests and pace.\n
                Commutes, coffee breaks, or just before bed — every moment becomes a chance to grow.\n
                📘 Smarter days start with smaller steps.\n
                Try MindSprint free for 7 days.
                """),

    AdModel(title="Кав’ярня “Дронова”",
            text="""
                Сучасна кава — це не просто смак, а зручність. У “Дроновій” ми поєднали справжню арабіку, обсмажену вручну, з високими технологіями.\n
                Замовляй через застосунок, і наш дрон доставить свіжозварену каву в парк, на лавку біля офісу чи навіть на дах твого будинку.\n
                ☕️ Гаряча кава. Без черг. Без стресу.\n
                Ми не просто готуємо напій — ми даруємо хвилини затишку прямо туди, де ти є.\n
                """),

    AdModel(title="БатяVR — Село, яке завжди з тобою",
            text="""
                Втомився від шуму міста? “БатькоVR” переносить тебе у віртуальне українське село — з піччю, коровами, ранковою росою та співом жайворонків.\n
                Пройдися віртуальними стежками дитинства, послухай бабусині казки або підгодуй гусей. Це не гра — це емоційне перезавантаження.\n
                🧑‍🌾 Зроблено з любов’ю до українських коренів.\n
                Завантажуй додаток. Перемикай реальність.\n
                """),

    AdModel(title="ЗОВНІ — український бренд функціонального одягу",
            text="""
                Одяг, що тримає тепло, не промокає і витримує реалії нашої погоди — створений в Україні, для українців.\n
                Кожен елемент перевірено на фронті, у горах та під дощем. Ми поєднали тактичну надійність з міською естетикою.\n
                Ідеально для мандрівок, щоденних пригод або активного життя у великому місті.\n
                🧥 ЗОВНІ — твій захист зовні.\n
                Підтримай українське. Одягай силу.\n
                """)

]


def get_random_ad():
    return random.choice(ads)



@app.get("/auth/session")
async def check_session(Authorization: str | None = Cookie(default=None)):
    if Authorization:
        return {"authorized": True, "user_id": Authorization}
    else:
        return {"authorized": False}



@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")
    
    async with get_connection() as conn:

        posts = []

        if session_id:

            posts = await user_crud.get_user_feed(conn=conn, id=session_id)

            sorted_posts = await user_crud.sort_user_liked(conn=conn, user_id=session_id, posts=posts)

            if posts == None:
                posts = await user_crud.get_random_feed(conn=conn)

                sorted_posts = await user_crud.sort_user_liked(conn=conn, user_id=session_id, posts=posts)

        else:
            sorted_posts = await user_crud.get_random_feed(conn=conn)


    return templates.TemplateResponse(
        request=request, name="main.html", context={"session_id": session_id, "posts": sorted_posts, "advertisement": advertisement}
    )

@app.post("/register")
async def register(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()], 
                   birthday: Annotated[str, Form()], sex: Annotated[str, Form()]):


    async with get_connection() as conn:   
        await user_crud.create(conn=conn, data=create_user(username=username, unhashed_password=password, birthday=birthday, sex=sex))

        user_model = await user_crud.get_user(conn=conn, login=username)
        SESSION_ID = user_model.id
        
      
        response = RedirectResponse(request.url_for('me_profile'), status_code=status.HTTP_303_SEE_OTHER)

        response.set_cookie(key="Authorization", value=SESSION_ID, httponly=True, samesite='none', secure=True, expires=2592000)

        return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="reg-log_page.html"
    )

@app.post("/login")
async def login_form(request: Request, username: Annotated[str, Form()], password: Annotated[str, Form()]):
    
    async with get_connection() as conn:   
        user = await user_crud.authenticate(conn=conn, auth_data=AuthUserModel(username=username, password=password))

        response = RedirectResponse(request.url_for('read_main'), status_code=status.HTTP_303_SEE_OTHER)
        
        print(user)
        SESSION_ID = user.id
        response.set_cookie(key="Authorization", value=SESSION_ID, httponly=True, samesite='none', secure=True, expires=2592000)

        return response


@app.post("/logout")
async def logout(response: Response, request: Request):

    
    response = RedirectResponse(request.url_for('read_main'), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="Authorization")

    return response


@app.post("/follow_user", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def follow_user(response: Response, request: Request, follows_username: Annotated[str, Form()]):

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:

        id = session_id
        user_follows = await user_crud.get_user(conn=conn, login=follows_username)

        user_self = await user_crud.get_user_by_id(conn=conn, id=id)

        await user_crud.follow(conn=conn, data=BaseFollowModel(id=id, follows=user_follows.id, follow_type="user"))
        await user_crud.write_user_notif(conn=conn, user_id=user_follows.id, notif_text=f"{user_self.username} now follows you!")

        response = RedirectResponse(f"/user/{user_follows.username}", status_code=status.HTTP_303_SEE_OTHER)

        return response

@app.post("/unfollow_user", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def unfollow_user(response: Response, request: Request, unfollows_username: Annotated[str, Form()]):

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:
        
        id = session_id
        user_follows = await user_crud.get_user(conn=conn, login=unfollows_username)

        await user_crud.unfollow(conn=conn, data=BaseFollowModel(id=id, follows=user_follows.id, follow_type="user"))

        response = RedirectResponse(f"/user/{user_follows.username}", status_code=status.HTTP_303_SEE_OTHER)
        return response

@app.post("/follow_thread", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def follow_thread(response: Response, request: Request, follow_thread_tag: Annotated[str, Form()]):

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:
        
        id = session_id
        follows = await user_crud.get_thread_by_tag(conn=conn, tag=follow_thread_tag)

        await user_crud.follow(conn=conn, data=BaseFollowModel(id=id, follows=follows.id, follow_type="thread"))

        response = RedirectResponse(f"/thread/{follow_thread_tag}", status_code=status.HTTP_303_SEE_OTHER)
        return response




@app.post("/unfollow_thread", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def unfollow_thread(response: Response, request: Request, unfollow_thread_tag: Annotated[str, Form()]):

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:
        
        id = session_id
        follows = await user_crud.get_thread_by_tag(conn=conn, tag=unfollow_thread_tag)

        await user_crud.unfollow(conn=conn, data=BaseFollowModel(id=id, follows=follows.id, follow_type="thread"))

        response = RedirectResponse(f"/thread/{unfollow_thread_tag}", status_code=status.HTTP_303_SEE_OTHER)
        return response



@app.get("/createpost", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def createpost_page(request: Request):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:
        user_model = await user_crud.get_user_by_id(conn=conn, id=session_id)
        followed_threads = await user_crud.get_user_followed_threads(conn=conn, data=user_model, follow_type="thread")


    return templates.TemplateResponse(
        request=request, name="create-post-page.html", context={"user": user_model, "followed_threads": followed_threads, "advertisement": advertisement}
    )


@app.post("/createpost", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def post_create(request: Request, title: Annotated[str, Form()], description: Annotated[str, Form()], location: Annotated[str, Form()], file: UploadFile = File(...)):

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:

        file_path = os.path.join("saving_files", file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

            file_extension = file.filename.split(".")[-1]

            user = await user_crud.get_user_by_id(conn=conn, id=session_id)

            await user_crud.create_post(conn=conn, data=UploadPostModel(title=title, desc=description, picture=file_path, 
                                                                author_id=user.id, file_extension=file_extension, location_id=location.split(":")[1],
                                                                author_str=user.username, location_str=location.split(":")[0]))
            
            buffer.close()
            os.remove(file_path)
        
        if location.split(":")[0] == user.username:

            response = RedirectResponse(request.url_for('me_profile'), status_code=status.HTTP_303_SEE_OTHER)
            return response
        
        else:

            thread_tag = location.split(":")[0]
            response = RedirectResponse(f"/thread/{thread_tag}", status_code=status.HTTP_303_SEE_OTHER)
            return response


@app.get("/me", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def me_profile(request: Request):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")

    async with get_connection() as conn:
        user = await user_crud.get_user_by_id(conn=conn, id=session_id)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
            
        posts = await user_crud.get_user_posts(conn=conn, author_id=user.id, location_id=user.id)

        sorted_posts = await user_crud.sort_user_liked(conn=conn, user_id=session_id, posts=posts)

        followers = len(await user_crud.get_user_followers_by_type(conn=conn, data=user, follow_type="user"))
        following = len(await user_crud.get_user_follows_by_type(conn=conn, data=user, follow_type="user"))
        friends = await user_crud.get_user_friends(conn=conn, self_user_id=user.id)

        if friends != "You have currently no friends":
            friends = len(friends)
        
        else:
            friends = 0
        
        return templates.TemplateResponse(
            request=request, name="profile.html", context={"user": user, "if_followed": "me_page", "followers": followers, "following": following, "friends": friends, "user_self": user, "session_id": session_id, "posts": sorted_posts, "advertisement": advertisement}
        )


@app.get("/me/edit", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def profile_edit(request: Request):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")

    async with get_connection() as conn:
        user = await user_crud.get_user_by_id(conn=conn, id=session_id)
               
        return templates.TemplateResponse(
            request=request, name="profile-edit_page.html", context={"user": user, "session_id": session_id, "advertisement": advertisement}
        )
    
@app.post("/me/edit", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def profile_edit(request: Request, new_username: Annotated[str, Form()], description: Annotated[str, Form()], 
                       avatar: UploadFile | None = File(None), 
                       banner: UploadFile | None = File(None)):

    session_id = request.cookies.get("Authorization")


    async with get_connection() as conn:

        if avatar.filename != "":
            avatar_path = os.path.join("saving_files", avatar.filename)
            with open(avatar_path, "wb") as buffer:
                buffer.write(await avatar.read())
                buffer.close()
        else:
            avatar_path = ""


        if banner.filename != "":
            banner_path = os.path.join("saving_files", banner.filename)
            with open(banner_path, "wb") as buffer:
                buffer.write(await banner.read())
                buffer.close()
        else:        
            banner_path = ""

        user = await user_crud.get_user_by_id(conn=conn, id=session_id)

        await user_crud.edit_profile(conn=conn, user_id=user.id, old_username=user.username, new_username=new_username, desc=description, avatar=avatar_path, banner=banner_path)  

        response = RedirectResponse(request.url_for('me_profile'), status_code=status.HTTP_303_SEE_OTHER)

        return response


@app.get("/thread/{thread_tag}", response_class=HTMLResponse)
async def thread_page(request: Request, thread_tag: str):
    
    session_id = request.cookies.get("Authorization")
    
    async with get_connection() as conn:
        thread_model = await user_crud.get_thread_by_tag(conn=conn, tag=thread_tag)



        if thread_model is None:
                raise HTTPException(status_code=404, detail="Thread not found")
        
        posts = await user_crud.get_thread_posts(conn=conn, location_id=thread_model.id)

        member_count = await user_crud.count_thread_members(conn=conn, thread_id=thread_model.id)
        post_count = await user_crud.count_thread_posts(conn=conn, thread_id=thread_model.id)


        if session_id:

            if_followed = await user_crud.get_user_followed(conn=conn, data=BaseFollowModel(id=session_id, follows=thread_model.id, follow_type="thread"))

            sorted_posts = await user_crud.sort_user_liked(conn=conn, user_id=session_id, posts=posts)

            if if_followed is not None:
                if_followed = True

            else:
                if_followed = False

        elif session_id is None:
            if_followed = False

            sorted_posts = posts

        return templates.TemplateResponse(
            request=request, name="thread_page.html", context={"session_id": session_id, "if_followed": if_followed, "thread": thread_model, "posts": sorted_posts, "if_followed": if_followed, "member_count": member_count, "post_count": post_count}
        )



@app.get("/thread-create", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def create_thread_page(request: Request):

    advertisement = get_random_ad()

    return templates.TemplateResponse(
        request=request, name="create-thread-page.html", context={"advertisement": advertisement}
    )


@app.post("/thread-create", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def create_thread(request: Request, name: Annotated[str, Form()], tag: Annotated[str, Form()], description: Annotated[str, Form()], avatar: UploadFile = File(...), banner: UploadFile = File(...)):

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:

        
        avatar_path = os.path.join("saving_files", avatar.filename)
        with open(avatar_path, "wb") as buffer:
            buffer.write(await avatar.read())
            buffer.close()

        banner_path = os.path.join("saving_files", banner.filename)
        with open(banner_path, "wb") as buffer:
            buffer.write(await banner.read())
            buffer.close()


        await user_crud.create_thread(conn=conn, data=UploadThreadModel(name=name, desc=description, avatar=avatar_path, 
                                                                  banner=banner_path, admin=session_id, tag=tag))
            
        os.remove(avatar_path)
        os.remove(banner_path)

        response = RedirectResponse(f"/thread/{"@" + tag}", status_code=status.HTTP_303_SEE_OTHER)
        return response


@app.get("/user/{username}", response_class=HTMLResponse)
async def user_profile(request: Request, username: str):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")


    async with get_connection() as conn:


        user_self = await user_crud.get_user_by_id(conn=conn, id=session_id)

        user = await user_crud.get_user(conn=conn, login=username)

        if user_self == None:
            posts = await user_crud.get_user_posts(conn=conn, author_id=user.id, location_id=user.id)

            sorted_posts = posts

            followers = len(await user_crud.get_user_followers_by_type(conn=conn, data=user, follow_type="user"))
            following = len(await user_crud.get_user_follows_by_type(conn=conn, data=user, follow_type="user"))

            friends = await user_crud.get_user_friends(conn=conn, self_user_id=user.id)

            if friends != "You have currently no friends":
                friends = len(friends)
            
            else:
                friends = 0

            return templates.TemplateResponse(
                request=request, name="profile.html", context={"user": user, "user_self": user_self, "if_followed": False, "followers": followers, "following": following, "friends": friends, "session_id": session_id, "posts": sorted_posts, "advertisement": advertisement}
            )

        if user_self.id == user.id:
            response = RedirectResponse("/me", status_code=status.HTTP_303_SEE_OTHER)
        

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
            
        posts = await user_crud.get_user_posts(conn=conn, author_id=user.id, location_id=user.id)

        sorted_posts = await user_crud.sort_user_liked(conn=conn, user_id=session_id, posts=posts)

        followers = len(await user_crud.get_user_followers_by_type(conn=conn, data=user, follow_type="user"))
        following = len(await user_crud.get_user_follows_by_type(conn=conn, data=user, follow_type="user"))
        friends = await user_crud.get_user_friends(conn=conn, self_user_id=user.id)

        if friends != "You have currently no friends":
            friends = len(friends)
        
        else:
            friends = 0



        if_followed = await user_crud.get_user_followed(conn=conn, data=BaseFollowModel(id=user_self.id, follows=user.id, follow_type=None))

        if if_followed is not None:
            if_followed = True

        else:
            if_followed = False

        print("Friends: ", friends)

        
        return templates.TemplateResponse(
            request=request, name="profile.html", context={"user": user, "user_self": user, "if_followed": if_followed, "followers": followers, "following": following, "friends": friends, "session_id": session_id, "posts": sorted_posts, "advertisement": advertisement}
        )



@app.get("/user/{username}/friends", response_class=HTMLResponse)
async def user_friends_page(request: Request, username: str):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")


    async with get_connection() as conn:
        user = await user_crud.get_user(conn=conn, login=username)

        friends = await user_crud.get_user_friends(conn=conn, self_user_id=user.id)
        followers = await user_crud.get_user_followers_by_type(conn=conn, data=user, follow_type="user")
        following = await user_crud.get_user_follows_by_type(conn=conn, data=user, follow_type="user")

        # print("User: ", user)
        # print("User friends: ", friends)

        return templates.TemplateResponse(
            request=request, name="other_friends_page.html", context={"user": user, "followers": followers, "following": following, "friends": friends, "session_id": session_id, "advertisement": advertisement}
        )
        
        


@app.get("/chat/{user2}", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def chat_with_user(request: Request, user2: str):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")

    async with get_connection() as conn:

        user1_model = await user_crud.get_user_by_id(conn=conn, id=session_id)
        user2_model = await user_crud.get_user(conn=conn, login=user2)

        if user2_model is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        chat_model = await user_crud.get_chat(conn=conn, user1=user1_model.username, user2=user2_model.username)
        messages = await user_crud.get_chat_messages(conn=conn, chat_id=chat_model.id)
            
        return templates.TemplateResponse(
            request=request, name="chat.html", context={"user1": user1_model, "user2": user2_model, "chat": chat_model, "messages": messages, "request": request, "advertisement": advertisement}
        )

@app.post("/createchat", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def create_chat(request: Request, user2: Annotated[str, Form()]):

    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:

        user1_model = await user_crud.get_user_by_id(conn=conn, id=session_id)
        user2_model = await user_crud.get_user(conn=conn, login=user2)

        await user_crud.create_chat(conn=conn, user1_id=user1_model.id, user1_str=user1_model.username, user2_id=user2_model.id, user2_str=user2_model.username)
            
        response = RedirectResponse(f"/chat/{user2_model.username}", status_code=status.HTTP_303_SEE_OTHER)
        return response


@app.post("/send_message", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def message_send(request: Request, chat_id: Annotated[str, Form()], message_text: Annotated[str, Form()], file: UploadFile | None = File(None)):
    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:

        user = await user_crud.get_user_by_id(conn=conn, id=session_id)


        if file.filename:
            file_path = os.path.join("saving_files", file.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

                file_extension = file.filename.split(".")[-1]

                await user_crud.create_message(conn=conn, data=UploadMessageModel(chat_id=chat_id, text=message_text, picture=file_path, 
                                                                    author_id=user.id, author_str=user.username, file_extension=file_extension))
                
                buffer.close()
                os.remove(file_path)

        else:
            await user_crud.create_message(conn=conn, data=UploadMessageModel(chat_id=chat_id, text=message_text, picture="", 
                                                                    author_id=user.id, author_str=user.username, file_extension=""))


    
    await manager.broadcast("new_message")



@app.post("/get_messages", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def messages_get(request: Request, chat_id: Annotated[str, Form()]):
    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:

        user1_model = await user_crud.get_user_by_id(conn=conn, id=session_id)
        messages_updated = await user_crud.get_chat_messages(conn=conn, chat_id=chat_id)

    print(messages_updated)

    return templates.TemplateResponse("chat_message_list.html", {"user1": user1_model, "messages": messages_updated, "request": request})



@app.get("/{location_str}/post/{post_id}", response_class=HTMLResponse)
async def post_page(request: Request, location_str: str, post_id: str):

    advertisement = get_random_ad()


    session_id = request.cookies.get("Authorization")
    async with get_connection() as conn:

        post = await user_crud.get_post_by_id(conn=conn, id=post_id)

        comments = await user_crud.get_comments_by_location(conn=conn, location_id=post.id)

        if session_id:
            user = await user_crud.get_user_by_id(conn=conn, id=session_id)
            sorted_post = await user_crud.sort_user_liked(conn=conn, user_id=session_id, posts=[post])


        else:
            user = None
            sorted_post = [post]

    return templates.TemplateResponse(
        request=request, name="threads_post_page.html", context={"session_id": session_id, "post": sorted_post[0], "comments": comments, "user": user, "advertisement": advertisement}
    )
    


@app.post("/create_comment", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def create_comment(request: Request, text: Annotated[str, Form()], post_id: Annotated[str, Form()], author_id: Annotated[str, Form()], 
                        author_str: Annotated[str, Form()], location_id: Annotated[str, Form()],
                        location_str: Annotated[str, Form()]):
    
    session_id = request.cookies.get("Authorization")

    if not session_id:
        return RedirectResponse("/", status_code=401)
    
    async with get_connection() as conn:
        await user_crud.create_comment(conn=conn, data=UploadCommentModel(text=text, author_id=author_id, 
                                author_str=author_str, location_id=location_id, location_str=location_str))
    
    return RedirectResponse(f"{location_str}/{post_id}", status_code=303)



@app.post("/like", dependencies=[Depends(get_auth_user)])
async def like(request: Request, payload: LikeRequest):
    
    session_id = request.cookies.get("Authorization")
    
    async with get_connection() as conn:
        await user_crud.like(conn=conn, author_id=session_id, post_id=payload.post_id)
        print("\npost liked\n")




@app.post("/unlike", dependencies=[Depends(get_auth_user)])
async def unlike(request: Request, payload: LikeRequest):
    
    session_id = request.cookies.get("Authorization")
    
    async with get_connection() as conn:
        await user_crud.unlike(conn=conn, author_id=session_id, post_id=payload.post_id)
        print("\npost unliked\n")



@app.post("/get_search_results", response_class=HTMLResponse)
async def get_search_results(request: Request, query: Annotated[str, Form()], category: Annotated[str, Form()]):

    async with get_connection() as conn:
        if category == "all":  
            results = await user_crud.search_all(conn=conn, query=query)
        
        if category == "posts":  
            results = await user_crud.search_posts(conn=conn, query=query)
        
        if category == "threads":  
            results = await user_crud.search_threads(conn=conn, query=query)
        
        if category == "users":  
            results = await user_crud.search_users(conn=conn, query=query)


    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "results": results,
        "category": category
    })



# сделать белую тему, так чтобы все элементы становились белыми, но чтобы все работало, просто люти флэшбэнг


@app.get("/friends", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def friends_page(request: Request):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")

    async with get_connection() as conn:

        user_self = await user_crud.get_user_by_id(conn=conn, id=session_id)

        if user_self is None:
            raise HTTPException(status_code=404, detail="User not found")
            
        friends_models = await user_crud.get_user_friends(conn=conn, self_user_id=user_self.id)
        print(friends_models)

        return templates.TemplateResponse(
            request=request, name="friends_page.html", context={"user": user_self, "session_id": session_id, "friends": friends_models, "advertisement": advertisement}
        )



@app.get("/threads", response_class=HTMLResponse)
async def read_item(request: Request):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")

    async with get_connection() as conn:
        threads = await user_crud.get_threads(conn=conn)

        
    return templates.TemplateResponse(
        request=request, name="threads-list.html", context={"session_id": session_id, "threads": threads, "advertisement": advertisement}
    )


@app.get("/settings", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="settings_page.html", context={}
    )


@app.get("/notifications", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def read_item(request: Request):

    advertisement = get_random_ad()
    session_id = request.cookies.get("Authorization")

    async with get_connection() as conn:
        notifications = await user_crud.get_user_notifs(conn=conn, user_id=session_id)

    return templates.TemplateResponse(
        request=request, name="notifications.html", context={"session_id": session_id, "advertisement": advertisement, "notifications": notifications}
    )




@app.get("/delete_old_notifs", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def delete_old_notifs(request: Request):

    async with get_connection() as conn:
        await user_crud.delete_old_notifs(conn=conn)


@app.post("/delete_post", response_class=HTMLResponse, dependencies=[Depends(get_auth_user)])
async def delete_post(response: Response, request: Request, post_id: Annotated[str, Form()], redirect_link: Annotated[str, Form()]):
    
    session_id = request.cookies.get("Authorization")


    async with get_connection() as conn:
        message = await user_crud.delete_post(conn=conn, user_id=session_id, post_id=post_id)

    if not message:
        response = RedirectResponse(f"{redirect_link}", status_code=status.HTTP_303_SEE_OTHER)
        return response

    else:
        response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        return response

@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request):

    advertisement = get_random_ad()

    session_id = request.cookies.get("Authorization")

    async with get_connection() as conn:
        values = await user_crud.leaderboard_get_values(conn=conn)

    return templates.TemplateResponse(
        request=request, name="leaderboard.html", context={"session_id": session_id, "values": values, "advertisement": advertisement}
    )

@app.get("/leaderboard/update", response_class=HTMLResponse)
async def leaderboard_update(request: Request):

    async with get_connection() as conn:
        await user_crud.leaderboard_update_values(conn=conn)
        
    return RedirectResponse("/leaderboard", status_code=303)


