import psycopg
from psycopg import sql
from typing import Iterator
import models.user as models
from core import passwords
from crud import authenticate as crud_auth, upload_image, create_thread, create_message, upload_avatar, upload_banner, create_comment
import uuid
from time import mktime
from datetime import datetime, timezone, timedelta
import random
from core.lang import lang_detect



class UserCRUD:
    async def create(self, conn: Iterator[psycopg.Connection], data: models.RegistrationModel) -> None:
        cur = conn.cursor()

        try:
            user = await self.get_user(conn, data.username)
            if user is not None:
                raise TypeError(f"User with login {data.username} already exists")

            language = lang_detect(data.description)
            await cur.execute(

                """INSERT INTO "User" VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, to_tsvector(%s, coalesce(%s, '') || ' ' || coalesce(%s, '')))""",
                (data.user_id, data.username, data.birthday, data.register_date, data.password, 
                data.achievements, data.last_time_active, data.sex, data.avatar, data.banner, data.description, data.status, language, language, data.username, data.description,)
            )

            await conn.commit()

        finally:
            await cur.close()

    
    async def set_user_status(self, conn, user_id: str, status: str):
        cur = conn.cursor()

        try:
            await cur.execute(
                'UPDATE public."User" SET status=%s WHERE id=%s', (status, user_id,)
            )

            await conn.commit()

        finally:
            await cur.close()



    async def edit_profile(self, conn, user_id, old_username, new_username, desc, avatar, banner) -> None:
        cur = conn.cursor()

        try:
            user = await self.get_user(conn=conn, login=new_username)
            if user is not None:
                if user.username != old_username:
                    raise TypeError("A user with such username already exists")
            
            if avatar != "":
                avatar_uploaded = upload_avatar(avatar_path=avatar)
            else:
                avatar_uploaded = avatar


            if banner != "":
                banner_uploaded = upload_banner(banner_path=banner)
            else:
                banner_uploaded = banner


            update_data = {
                "username": new_username,
                "description": desc,
                "avatar": avatar_uploaded,
                "banner": banner_uploaded
            }
            

            filtered_data = {k: v for k, v in update_data.items() if v not in (None,)}

            if filtered_data:
                set_clauses = ", ".join([f"{key} = %({key})s" for key in filtered_data])
                query = f"""
                    UPDATE public."User"
                    SET {set_clauses}
                    WHERE id = %(user_id)s
                """

                filtered_data["user_id"] = user_id

                await cur.execute(query, filtered_data)


            await conn.commit()

            await self.update_tsv_user(conn=conn, new_username=new_username, new_desc=desc, id=user_id)

            print("\ntsv updated (User)\n")

        finally:
            await cur.close()


    async def authenticate(self, conn, auth_data) -> models.UserModel:
        cur = conn.cursor()
        try:
            await cur.execute(
                'SELECT "User".password FROM public."User" WHERE username=%s', (auth_data.username,)
            )
            row = await cur.fetchone()

            crud_auth(auth_data, row)

            return await self.get_user(conn, auth_data.username)
        finally:
            await cur.close()

    async def get_user(self, conn, login: str):
        cur = conn.cursor()

        try:
            await cur.execute(
                """
                SELECT "User".id, "User".username, "User".birthday, "User".register_date, "User".achievements, 
                "User".last_time_active, "User".sex, "User".avatar, "User".banner, "User".description, "User".status
                FROM public."User" 
                WHERE username=%s
                """,
                (login,)
            )
            row = await cur.fetchone()

            if row is None:
                return None
            
            id, username, birthday, register_date, achievements, last_time_active, sex, avatar, banner, description, status = row


            avatar_link = avatar
            banner_link = avatar

            if avatar == "":
                avatar_link = "/static/images/profile-pic.png"
        
            if banner == "":
                banner_link = "/static/images/profile_background.png"

            return models.BaseUserModel(id=id, username=username, birthday=birthday, register_date=register_date, achievements=achievements,
                                last_time_active=last_time_active, sex=sex, avatar=avatar_link, banner=banner_link, description=description, status=status)
        
        finally:
            await cur.close()

    
    async def get_user_by_id(self, conn, id: str) -> models.BaseUserModel | None:
        cur = conn.cursor()

        try:
            await cur.execute(
                """
                SELECT "User".id, "User".username, "User".birthday, "User".register_date, "User".achievements, 
                "User".last_time_active, "User".sex, "User".avatar, "User".banner, "User".description, "User".status
                FROM public."User"
                WHERE id=%s
                """,
                (id,)
            )
            row = await cur.fetchone()

            if row is None:
                return None

            id, username, birthday, register_date, achievements, last_time_active, sex, avatar, banner, description, status = row

            if id is None:
                return None
            
            avatar_link = avatar
            banner_link = avatar

            if avatar == "":
                avatar_link = "/static/images/profile-pic.png"
        
            if banner == "":
                banner_link = "/static/images/profile_background.jfif"

            return models.BaseUserModel(id=id, username=username, birthday=birthday, register_date=register_date, achievements=achievements,
                                last_time_active=last_time_active, sex=sex, avatar=avatar_link, banner=banner_link, description=description, status=status)
        finally:
            await cur.close()


    async def create_post(self, conn, data):
        cur = conn.cursor()
        try:

            post_data = upload_image(data)
            language = lang_detect(post_data.title)

            await cur.execute(
                """INSERT INTO "Post" VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, to_tsvector(%s, coalesce(%s, '') || ' ' || coalesce(%s, '')))""",
                (post_data.id, post_data.title, post_data.desc, post_data.picture, post_data.likes, 
                post_data.comms, post_data.author_id, post_data.date_created, post_data.file_extension, 
                post_data.location_id, post_data.author_str, post_data.location_str, language, language, post_data.title, post_data.desc,)
            )

            await conn.commit()

        finally:
            await cur.close()


    
    async def get_user_posts(self, conn, author_id, location_id) -> list[models.BasePostModel]:
        cur = conn.cursor()
        try:
            await cur.execute(
                """
                SELECT "Post".id, "Post".title, "Post".description, "Post".picture, "Post".author_id,
                "Post".date_created, "Post".file_extension, "Post".location_id, "Post".author_str, "Post".location_str,
                "Post".language, "Post".tsv, "User".avatar, "Thread".avatar, COALESCE("Like".likes, 0) AS likes, COALESCE("Comment".comms, 0) AS comms
                FROM public."Post"
                LEFT JOIN public."User"
                ON "Post".author_id="User".id
                LEFT JOIN public."Thread"
                ON "Post".location_id="Thread".id
				LEFT JOIN (SELECT post_id, COUNT(*) AS likes FROM public."Like" GROUP BY post_id) "Like"
    			ON "Post".id = "Like".post_id
				LEFT JOIN (SELECT location_id, COUNT(*) AS comms FROM public."Comment" GROUP BY location_id) "Comment"
    			ON "Post".id = "Comment".location_id
				
                WHERE "Post".author_id=%s AND "Post".location_id=%s
                """, (author_id, location_id,)
            )


            rows = await cur.fetchall()

            if rows is None:
                return None
            
            posts = []
            for row in rows:
            
                id, title, desc, picture, author_id, date_created, file_extension, location_id, author_str, location_str, language, tsv, user_avatar, thread_avatar, likes, comms = row

                avatar = user_avatar

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"
                
                if thread_avatar != None:
                    avatar = thread_avatar

                posts.append(models.BasePostModel(
                    id=id,
                    title=title,
                    desc=desc,
                    picture=picture,
                    likes=likes,
                    comms=comms,
                    author_id=author_id,
                    date_created=date_created,
                    file_extension=file_extension,
                    location_id=location_id,
                    author_str=author_str,
                    location_str=location_str,
                    avatar=avatar
                ))
            
            return posts

        finally:
            await cur.close()

    
        
    async def get_random_feed(self, conn) -> list[models.BasePostModel]:
        cur = conn.cursor()
        try:
            await cur.execute(
                """
                SELECT "Post".id, "Post".title, "Post".description, "Post".picture, "Post".author_id,
                "Post".date_created, "Post".file_extension, "Post".location_id, "Post".author_str, "Post".location_str,
                "Post".language, "Post".tsv, "User".avatar, "Thread".avatar, COALESCE("Like".likes, 0) AS likes, COALESCE("Comment".comms, 0) AS comms
                FROM public."Post"
                LEFT JOIN public."User"
                ON "Post".author_id="User".id
                LEFT JOIN public."Thread"
                ON "Post".location_id="Thread".id
				LEFT JOIN (SELECT post_id, COUNT(*) AS likes FROM public."Like" GROUP BY post_id) "Like"
    			ON "Post".id = "Like".post_id
				LEFT JOIN (SELECT location_id, COUNT(*) AS comms FROM public."Comment" GROUP BY location_id) "Comment"
    			ON "Post".id = "Comment".location_id
				
                """, ()
            )

            rows = await cur.fetchall()

            if rows == []:
                return None
            
            posts = []

            rows_list = [x for x in rows]

            for row in rows_list:

                choosed = random.choice(rows_list)
            
                id, title, desc, picture, author_id, date_created, file_extension, location_id, author_str, location_str, language, tsv, user_avatar, thread_avatar, likes, comms = choosed

                avatar = user_avatar

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"
                
                if thread_avatar != None:
                    avatar = thread_avatar

                posts.append(models.BasePostModel(
                    id=id,
                    title=title,
                    desc=desc,
                    picture=picture,
                    likes=likes,
                    comms=comms,
                    author_id=author_id,
                    date_created=date_created,
                    file_extension=file_extension,
                    location_id=location_id,
                    author_str=author_str,
                    location_str=location_str,
                    avatar=avatar
                ))

            rows_list.pop(rows_list.index(choosed))
            
            return posts
                

        finally:
            await cur.close()
            

    async def follow(self, conn, data):
        cur = conn.cursor()
        try:
            if await self.get_user_followed(conn=conn, data=data) is not None:
                raise TypeError("You are already following this user")
            
            if data.id == data.follows:
                raise TypeError("You can't follow yourself")
            
            await cur.execute(
                'INSERT INTO "Follow" VALUES(%s, %s, %s)', (data.id, data.follows, data.follow_type,)
            )

            await conn.commit()

        finally:
            await cur.close()

    async def unfollow(self, conn, data):
        cur = conn.cursor()
        try:
            if await self.get_user_followed(conn=conn, data=data) is None:
                raise TypeError("You are not following this user")
            
            if data.id == data.follows:
                raise TypeError("You can't unfollow yourself")
            
            await cur.execute(
                'DELETE FROM public."Follow" WHERE id=%s AND follows=%s AND follow_type=%s', (data.id, data.follows, data.follow_type,)
            )

            await conn.commit()

        finally:
            await cur.close()

    async def get_user_followed(self, conn, data):
        cur = conn.cursor()
        try:
            await cur.execute(
                'SELECT * FROM public."Follow" WHERE id=%s AND follows=%s', (data.id, data.follows,)
            )

            row = await cur.fetchone()
            return row
        
        finally:
            await cur.close()
        
    

    async def get_user_follows_by_type(self, conn, data: models.BaseUserModel, follow_type: str):
        cur = conn.cursor()
        try:
            await cur.execute(
                'SELECT * FROM public."Follow" WHERE id=%s AND follow_type=%s', (data.id, follow_type,)
            )

            rows = await cur.fetchall()
        
            entities_followed = []
            for row in rows:
                id, follows, followtype = row

                entities_followed.append(models.BaseFollowModel(
                    id=id,
                    follows=follows,
                    follow_type=followtype
                ))
            
            return entities_followed
        
        finally:
            await cur.close()

    
    async def get_user_followers_by_type(self, conn, data: models.BaseUserModel, follow_type: str):
        cur = conn.cursor()
        try:
            await cur.execute(
                'SELECT * FROM public."Follow" WHERE follows=%s AND follow_type=%s', (data.id, follow_type,)
            )

            rows = await cur.fetchall()
        
            entities_followed = []
            for row in rows:
                id, follows, followtype = row

                entities_followed.append(models.BaseFollowModel(
                    id=id,
                    follows=follows,
                    follow_type=followtype
                ))
            
            return entities_followed
        
        finally:
            await cur.close()
    

    
    async def get_user_followed_threads(self, conn, data: models.BaseUserModel, follow_type: str):
        cur = conn.cursor()
        try:
            threads = await self.get_user_follows_by_type(conn=conn, data=data, follow_type=follow_type)

            output = []
            for thread in threads:

                await cur.execute(
                    'SELECT "Thread".id, "Thread".tag FROM public."Thread" WHERE id=%s', (thread.follows,)
                )
                row = await cur.fetchone()

                id, tag = row
                output.append(models.ShowThreadTag(id=id, tag=tag))
            
            return output
        
        finally:
            await cur.close()


    async def get_user_feed(self, conn, id: str) -> list[models.BasePostModel]:
        cur = conn.cursor()
        try:
            await cur.execute(
                'SELECT "Follow".follows FROM public."Follow" WHERE id=%s', (id,)
            )

            follows = await cur.fetchall()

            if follows == []:
                return None

            posts = []
            follows_list = []

            for follow in follows:
                for x in follow:
                    follows_list.append(x)


    
            await cur.execute(
                """
                SELECT "Post".id, "Post".title, "Post".description, "Post".picture, "Post".author_id,
                "Post".date_created, "Post".file_extension, "Post".location_id, "Post".author_str, "Post".location_str,
                "Post".language, "Post".tsv, "User".avatar, "Thread".avatar, COALESCE("Like".likes, 0) AS likes, COALESCE("Comment".comms, 0) AS comms
                FROM public."Post"
                LEFT JOIN public."User"
                ON "Post".author_id="User".id
                LEFT JOIN public."Thread"
                ON "Post".location_id="Thread".id
				LEFT JOIN (SELECT post_id, COUNT(*) AS likes FROM public."Like" GROUP BY post_id) "Like"
    			ON "Post".id = "Like".post_id
				LEFT JOIN (SELECT location_id, COUNT(*) AS comms FROM public."Comment" GROUP BY location_id) "Comment"
    			ON "Post".id = "Comment".location_id

                WHERE "Post".location_id=ANY(%s)
                ORDER BY TO_TIMESTAMP("Post".date_created, 'DD.MM.YY HH24:MI') DESC
                """, (follows_list,)
            )

            rows = await cur.fetchall()

            if rows == []:
                return None
            
            posts = []

            for row in rows:
                id, title, desc, picture, author_id, date_created, file_extension, location_id, author_str, location_str, language, tsv, user_avatar, thread_avatar, likes, comms = row

                avatar = user_avatar

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"
                
                if thread_avatar != None:
                    avatar = thread_avatar

                posts.append(models.BasePostModel(
                    id=id,
                    title=title,
                    desc=desc,
                    picture=picture,
                    likes=likes,
                    comms=comms,
                    author_id=author_id,
                    date_created=date_created,
                    file_extension=file_extension,
                    location_id=location_id,
                    author_str=author_str,
                    location_str=location_str,
                    avatar=avatar
                ))

            
            return posts
        
        
        finally:
            await cur.close()
    

    async def create_thread(self, conn, data: models.UploadThreadModel):
        cur = conn.cursor()
        try:
 
            thread_data = create_thread(data)

            language = lang_detect(thread_data.desc)

            await cur.execute(
                'INSERT INTO "Thread" VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, to_tsvector(%s, coalesce(%s, '') || ' ' || coalesce(%s, '')))',
                (thread_data.id, thread_data.name, thread_data.desc, thread_data.avatar, thread_data.banner, 
                thread_data.members, thread_data.posts, thread_data.admin, thread_data.date_created, thread_data.tag, language, language, thread_data.name, thread_data.desc,)
            )

            await conn.commit()

        finally:
            await cur.close()

    
    async def get_threads(self, conn) -> list[models.BaseThreadModel]:
        cur = conn.cursor()

        try:
            await cur.execute(
                'SELECT * FROM public."Thread"'
                'ORDER BY members DESC', ()
            )
            rows = await cur.fetchall()

            if rows == []:
                return None
                
            
            threads = []
            for row in rows:

                id, name, desc, avatar, banner, members, posts, admin, date_created, tag, language, tsv = row

                avatar_link = avatar
                banner_link = banner

                threads.append(models.BaseThreadModel(id=id, name=name, desc=desc, avatar=avatar_link, banner=banner_link, 
                                    members=members, posts=posts, admin=admin, date_created=date_created, tag=tag))
            
            return threads
        
        finally:
            await cur.close()


    async def get_thread_by_tag(self, conn, tag: str):
        cur = conn.cursor()

        try:
            await cur.execute(
                'SELECT * FROM public."Thread" '
                'WHERE tag=%s',
                (tag,)
            )
            row = await cur.fetchone()

            if row is None:
                return None

            if tag is None:
                return None

            id, name, desc, avatar, banner, members, posts, admin, date_created, tag, language, tsv = row

            avatar_link = avatar
            banner_link = banner

            return models.BaseThreadModel(id=id, name=name, desc=desc, avatar=avatar_link, banner=banner_link, 
                                   members=members, posts=posts, admin=admin, date_created=date_created, tag=tag)
        
        finally:
            await cur.close()


    async def get_thread_posts(self, conn, location_id) -> list[models.BasePostModel]:
        cur = conn.cursor()
        try:
    
            await cur.execute(
                """
                SELECT "Post".id, "Post".title, "Post".description, "Post".picture, "Post".author_id,
                "Post".date_created, "Post".file_extension, "Post".location_id, "Post".author_str, "Post".location_str,
                "Post".language, "Post".tsv, "User".avatar, "Thread".avatar, COALESCE("Like".likes, 0) AS likes, COALESCE("Comment".comms, 0) AS comms
                FROM public."Post"
                LEFT JOIN public."User"
                ON "Post".author_id="User".id
                LEFT JOIN public."Thread"
                ON "Post".location_id="Thread".id
				LEFT JOIN (SELECT post_id, COUNT(*) AS likes FROM public."Like" GROUP BY post_id) "Like"
    			ON "Post".id = "Like".post_id
				LEFT JOIN (SELECT location_id, COUNT(*) AS comms FROM public."Comment" GROUP BY location_id) "Comment"
    			ON "Post".id = "Comment".location_id

                WHERE "Post".location_id=%s
                """, (location_id,)
            )

            rows = await cur.fetchall()

            if rows == []:
                return None
            
            posts = []

            for row in rows:
                id, title, desc, picture, author_id, date_created, file_extension, location_id, author_str, location_str, language, tsv, user_avatar, thread_avatar, likes, comms = row

                avatar = user_avatar

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"
                
                if thread_avatar != None:
                    avatar = thread_avatar

                posts.append(models.BasePostModel(
                    id=id,
                    title=title,
                    desc=desc,
                    picture=picture,
                    likes=likes,
                    comms=comms,
                    author_id=author_id,
                    date_created=date_created,
                    file_extension=file_extension,
                    location_id=location_id,
                    author_str=author_str,
                    location_str=location_str,
                    avatar=avatar
                ))

            
            return posts
        

        finally:
            await cur.close()


    
    async def create_chat(self, conn, user1_id, user1_str, user2_id, user2_str):
        cur = conn.cursor()
        try:
            cond = await self.get_chat(conn=conn, user1=user1_str, user2=user2_str)
            if cond is None:
                if user1_id == user2_id:
                    raise TypeError("You can't chat with yourself")
            
                data = models.BaseChatModel(
         
                    id=str(uuid.uuid4()),
                    user1_id=user1_id,
                    user1_str=user1_str,
                    user2_id=user2_id,
                    user2_str=user2_str
        
                )
            
                await cur.execute(
                    'INSERT INTO "Chat" VALUES(%s, %s, %s, %s, %s)',
                    (data.id, data.user1_id, data.user1_str, data.user2_id, data.user2_str,)
                ) 
            
                await conn.commit()

        finally:
            await cur.close()


    async def get_chat(self, conn, user1: str, user2: str):
        cur = conn.cursor()

        try:
            await cur.execute(
                'SELECT * FROM public."Chat" '
                'WHERE(user1_str=%s AND user2_str=%s) OR (user1_str=%s AND user2_str=%s)',
                (user1, user2, user2, user1,)
            )
            row = await cur.fetchone()

            if row is None:
                return None

            id, user1_id, user1_str, user2_id, user2_str = row


            return models.BaseChatModel(id=id, user1_id=user1_id, user1_str=user1_str, user2_id=user2_id, user2_str=user2_str)
        
        finally:
            await cur.close()


    async def get_chat_messages(self, conn, chat_id):
        cur = conn.cursor()
        try:
            await cur.execute(
                """SELECT "Message".id, "Message".chat_id, "Message".text, "Message".picture, "Message".author_id, "Message".author_str, 
                TO_CHAR(date_created::timestamp, 'DD.MM.YYYY') AS date_created, TO_CHAR(date_created::timestamp, 'HH24:MI') AS date_time_created, 
                "Message".file_extension FROM public."Message" WHERE chat_id=%s ORDER BY "Message".date_created DESC""", (chat_id,)
            )

            rows = await cur.fetchall()

            if rows is None:
                return None
            
            messages = []
            for row in rows:
                id, chat_id, text, picture, author_id, author_str, date_created, date_time_created, file_extension = row

                if picture != "":
                    picture_link = picture
                else:
                    picture_link = picture

                messages.append(models.BaseMessageModel(
                    id=id,
                    chat_id=chat_id,
                    text=text,
                    picture=picture_link,
                    author_id=author_id,
                    author_str=author_str,
                    date_created=date_created,
                    date_time_created=date_time_created,
                    file_extension=file_extension
                ))
            
            return messages

        finally:
            await cur.close()


    async def create_message(self, conn, data):
        cur = conn.cursor()
        try:
            message_data = create_message(data) 
            await cur.execute(
                'INSERT INTO "Message" VALUES(%s, %s, %s, %s, %s, %s, now(), %s)',
                (message_data.id, message_data.chat_id, message_data.text, message_data.picture, 
                 message_data.author_id,  message_data.author_str,  message_data.file_extension,)
            )

            await conn.commit()
            
        finally:
            await cur.close()
    

    async def get_user_friends(self, conn, self_user_id: str):
        cur = conn.cursor()
        try:
            await cur.execute(
                'SELECT "Follow".id FROM public."Follow" WHERE follows=%s AND follow_type=%s', (self_user_id, "user",)
            )

            followers = await cur.fetchall()

            if followers == []:
                return "You have currently no friends"

            friends_list = []

            for follower in followers:
                
                await cur.execute(
                    'SELECT "Follow".id FROM public."Follow" WHERE id=%s AND follows=%s AND follow_type=%s', (follower[0], self_user_id, "user",)
                )

                row = await cur.fetchone()

                if row is None:
                    return "You have currently no friends"
                
                friends_list.append(row[0])

            friends_models = []

            for friend_id in friends_list:
                friend_model = await self.get_user_by_id(conn=conn, id=friend_id)
                friends_models.append(friend_model)

            return friends_models

        
        finally:
            await cur.close()


    async def create_comment(self, conn, data):
        cur = conn.cursor()
        try:
            comment_data = create_comment(data)
            await cur.execute(
                'INSERT INTO "Comment" VALUES(%s, %s, now(), %s, %s, %s, %s, %s)',
                (comment_data.id, comment_data.text, comment_data.author_id,  comment_data.author_str,
                 comment_data.location_id, comment_data.location_str, comment_data.likes,)
            ) 

            await conn.commit()
            
        finally:
            await cur.close()


    
    async def like(self, conn, author_id, post_id):
        cur = conn.cursor()
        try:

            await cur.execute(
                'INSERT INTO "Like" VALUES(%s, %s, %s)',
                (uuid.uuid4(), author_id, post_id,)
            ) 

            await conn.commit()
            
        finally:
            await cur.close()

    
    async def sort_user_liked(self, conn, user_id: str , posts: list[models.BasePostModel]) -> list[models.BasePostModel]:
        cur = conn.cursor()
        try:

            await cur.execute(
                """
                SELECT * FROM public."Like"
                WHERE author_id=%s
                """,
                (user_id,)
            ) 

            rows = await cur.fetchall()

            if rows == []:
                return posts
            
            liked_post_ids = [row[2] for row in rows]
            
            if posts == [] or posts is None:
                return None
            
            for post in posts:
                post.liked_by_user = post.id in liked_post_ids

            
            return posts
            
        finally:
            await cur.close()

    
    async def unlike(self, conn, author_id, post_id):
        cur = conn.cursor()
        try:
            await cur.execute(
                'DELETE FROM "Like" WHERE author_id=%s AND post_id=%s', (author_id, post_id,)
            ) 

            await conn.commit()
            
        finally:
            await cur.close()



    async def delete_comment(self, conn, id):
        cur = conn.cursor()
        try:
            await cur.execute(
                'DELETE FROM "Comment" WHERE id=%s', (id,)
            ) 

            await conn.commit()
            
        finally:
            await cur.close()

    
    async def get_post_by_id(self, conn, id) -> models.BasePostModel:
        cur = conn.cursor()
        try:
            await cur.execute(
                """
                SELECT "Post".id, "Post".title, "Post".description, "Post".picture, "Post".author_id,
                "Post".date_created, "Post".file_extension, "Post".location_id, "Post".author_str, "Post".location_str,
                "Post".language, "Post".tsv, "User".avatar, "Thread".avatar, COALESCE("Like".likes, 0) AS likes, COALESCE("Comment".comms, 0) AS comms
                FROM public."Post"
                LEFT JOIN public."User"
                ON "Post".author_id="User".id
                LEFT JOIN public."Thread"
                ON "Post".location_id="Thread".id
				LEFT JOIN (SELECT post_id, COUNT(*) AS likes FROM public."Like" GROUP BY post_id) "Like"
    			ON "Post".id = "Like".post_id
				LEFT JOIN (SELECT location_id, COUNT(*) AS comms FROM public."Comment" GROUP BY location_id) "Comment"
    			ON "Post".id = "Comment".location_id
				
				WHERE "Post".id=%s
                """, (id,)
            )

            row = await cur.fetchone()

    
            if row is None:
                return None
            
            id, title, desc, picture, author_id, date_created, file_extension, location_id, author_str, location_str, language, tsv, user_avatar, thread_avatar, likes, comms = row

            avatar = user_avatar

            if avatar == "":
                avatar = "/static/images/profile-pic.png"

            if thread_avatar != None:
                avatar = thread_avatar

            return models.BasePostModel(
                id=id,
                title=title,
                desc=desc,
                picture=picture,
                likes=likes,
                comms=comms,
                author_id=author_id,
                date_created=date_created,
                file_extension=file_extension,
                location_id=location_id,
                author_str=author_str,
                location_str=location_str,
                avatar=avatar
            )
            

        finally:
            await cur.close()
    


    async def get_comments_by_location(self, conn, location_id) -> list[models.BaseCommentModel]:
        cur = conn.cursor()
        try:
            await cur.execute(
                """
                SELECT "Comment".id, "Comment".text, "Comment".author_id, "Comment".author_str, "Comment".location_id, "Comment".location_str, "Comment".likes, 
                TO_CHAR(date_created::timestamp, 'DD.MM.YYYY HH24:MI') AS date_created, "User".avatar
                FROM public."Comment"
                LEFT JOIN public."User"
                ON "User".id="Comment".author_id 
                WHERE "Comment".location_id=%s
                ORDER BY date_created DESC
                """, (location_id,)
            )

            rows = await cur.fetchall()

            if rows is None:
                return None
            
            comments = []
            for row in rows:
                id, text, author_id, author_str, location_id, location_str, likes, date_created, avatar = row
                
                if avatar == "":
                    avatar = "/static/images/profile-pic.png"

                comments.append(models.BaseCommentModel(
                    id=id,
                    text=text,
                    date_created=date_created,
                    author_id=author_id,
                    author_str=author_str,
                    location_id=location_id,
                    location_str=location_str,
                    likes=likes,
                    avatar=avatar                    
                ))
            
            return comments

        finally:
            await cur.close()
    

    async def leaderboard_get_values(self, conn):
        cur = conn.cursor()
        try:
            await cur.execute(
                """
                SELECT "Leaderboard".username, "Leaderboard".value, "Leaderboard".avatar FROM public."Leaderboard" WHERE type='friends' ORDER BY value DESC
                """
            )

            rows = await cur.fetchall()

            friends = []
            if rows != []:
                for row in rows:
                    username, value, avatar = row

                    if value == 0:
                        continue

                    friends.append(models.LeaderboardValueModel(
                        username=username,
                        value=value,
                        avatar=avatar
                    ))
            


            await cur.execute(
                """
                SELECT "Leaderboard".username, "Leaderboard".value, "Leaderboard".avatar FROM public."Leaderboard" WHERE type='posts' ORDER BY value DESC
                """
            )

            rows = await cur.fetchall()

            posts = []
            if rows != []:
                for row in rows:
                    username, value, avatar = row

                    if value == 0:
                        continue

                    posts.append(models.LeaderboardValueModel(
                        username=username,
                        value=value,
                        avatar=avatar
                    ))
            

            await cur.execute(
                """
                SELECT "Leaderboard".username, "Leaderboard".value, "Leaderboard".avatar FROM public."Leaderboard" WHERE type='hours' ORDER BY value DESC
                """
            )

            rows = await cur.fetchall()

            hours = []
            if rows != []:
                for row in rows:
                    username, value, avatar = row

                    if value == 0:
                        continue
                    
                    
                    rounded = str(value / 3600).split(".")
                    hours_decimal = rounded[0] + "." + rounded[1][0]

                    hours.append(models.LeaderboardValueModel(
                        username=username,
                        value=hours_decimal,
                        avatar=avatar
                    ))

            return models.LeaderboardValueListModel(friends=friends, posts=posts, hours=hours)

        finally:
            await cur.close()


    async def leaderboard_update_values(self, conn):
        cur = conn.cursor()
        try:
            
            users_friends = await self.count_all_users_friends(conn=conn)
            users_posts = await self.count_all_users_posts(conn=conn)
            users_hours = await self.get_all_users_hours(conn=conn)

            await cur.execute(
                """
                DELETE FROM public."Leaderboard" 
                """
            )


            if users_friends != []:
                values = [
                    sql.SQL("({}, {}, {}, {})").format(
                        sql.Literal(x["username"]),
                        sql.Literal(x["friend_count"]),
                        sql.Literal(x["avatar"]),
                        sql.Literal("friends")
                    )
                    for x in users_friends
                ]

                query = sql.SQL('INSERT INTO "Leaderboard" (username, value, avatar, type) VALUES {}').format(
                    sql.SQL(', ').join(values)
                )

                await cur.execute(query)


            if users_posts != []:
                values = [
                    sql.SQL("({}, {}, {}, {})").format(
                        sql.Literal(x["username"]),
                        sql.Literal(x["post_count"]),
                        sql.Literal(x["avatar"]),
                        sql.Literal("posts")
                    )
                    for x in users_posts
                ]

                query = sql.SQL('INSERT INTO "Leaderboard" (username, value, avatar, type) VALUES {}').format(
                    sql.SQL(', ').join(values)
                )

                await cur.execute(query)
            

            if users_hours != []:
                values = [
                    sql.SQL("({}, {}, {}, {})").format(
                        sql.Literal(x["username"]),
                        sql.Literal(x["hour_count"]),
                        sql.Literal(x["avatar"]),
                        sql.Literal("hours")
                    )
                    for x in users_hours
                ]

                query = sql.SQL('INSERT INTO "Leaderboard" (username, value, avatar, type) VALUES {}').format(
                    sql.SQL(', ').join(values)
                )

                await cur.execute(query)
            
            await conn.commit()

        finally:
            await cur.close()
    

    async def count_all_users_friends(self, conn) -> list[dict]:
        cur = conn.cursor()
        try:

            await cur.execute(
                'SELECT "User".id, "User".username, "User".avatar FROM public."User"', ()
            )

            users = await cur.fetchall()

            friend_count_list = []

            for user in users:
                await cur.execute(
                    'SELECT "Follow".id FROM public."Follow" WHERE follows=%s AND follow_type=%s', (user[0], "user",)
                )

                followers = await cur.fetchall()

                if followers == []:
                    continue

                friends_list = []
                

                for follower in followers:
                    
                    await cur.execute(
                        'SELECT "Follow".follows FROM public."Follow" WHERE id=%s AND follows=%s AND follow_type=%s', (user[0], follower[0], "user",)
                    )

                    row = await cur.fetchone()

                    if row is None:
                        continue
                    
                    friends_list.append(row[0])

                user_friends = {}
                user_friends["username"] = user[1]
                user_friends["friend_count"] = len(friends_list)
                

                if user[2] != "":
                    user_friends["avatar"] = user[2]
                else:
                    user_friends["avatar"] = "/static/images/profile-pic.png"


                friend_count_list.append(user_friends)

            return friend_count_list

        
        finally:
            await cur.close()


    async def count_all_users_posts(self, conn) -> list[dict]:
        cur = conn.cursor()
        try:

            await cur.execute(
                'SELECT "User".id, "User".username, "User".avatar FROM public."User"', ()
            )

            users = await cur.fetchall()

            user_posts_count = []

            for user in users:
                await cur.execute(
                    'SELECT "Post".id FROM public."Post" WHERE author_id=%s ', (user[0],)
                )

                posts_list = await cur.fetchall()

                if posts_list == []:
                    continue


                user_posts = {}
                user_posts["username"] = user[1]
                user_posts["post_count"] = len(posts_list)
                

                if user[2] != "":
                    user_posts["avatar"] = user[2]
                else:
                    user_posts["avatar"] = "/static/images/profile-pic.png"


                user_posts_count.append(user_posts)

            return user_posts_count

        
        finally:
            await cur.close()



    async def get_all_users_hours(self, conn) -> list[dict]:
        cur = conn.cursor()
        try:

            await cur.execute(
                'SELECT "User".id, "User".username, "User".avatar FROM public."User"', ()
            )

            users = await cur.fetchall()

            user_hours_count = []

            for user in users:
                await cur.execute(
                    'SELECT "Hours".total_time FROM public."Hours" WHERE user_id=%s ', (user[0],)
                )

                hours = await cur.fetchone()

                if hours == []:
                    continue


                user_hours = {}
                user_hours["username"] = user[1]
                user_hours["hour_count"] = hours[0]

                if user[2] != "":
                    user_hours["avatar"] = user[2]
                else:
                    user_hours["avatar"] = "/static/images/profile-pic.png"


                user_hours_count.append(user_hours)

            return user_hours_count

        
        finally:
            await cur.close()
        

    async def count_thread_members(self, conn, thread_id) -> int:
        cur = conn.cursor()
        try:

            await cur.execute(
                """SELECT "Follow".id FROM public."Follow" WHERE follows=%s and follow_type='thread' """, (thread_id,)
            )

            members = await cur.fetchall()

            return len(members)
        
        finally:
            await cur.close()

    
    async def count_thread_posts(self, conn, thread_id) -> int:
        cur = conn.cursor()
        try:
                
            await cur.execute(
                'SELECT "Post".id FROM public."Post" WHERE location_id=%s ', (thread_id,)
            )

            posts = await cur.fetchall()

            return len(posts)

        finally:
            await cur.close()



    async def write_user_time(self, conn, user_id, duration):
        cur = conn.cursor()
        try:
            await cur.execute("""SELECT total_time FROM public."Hours" WHERE user_id = %s""", (user_id,))
            row = await cur.fetchone()

            if row:
                total_time = row[0] + duration
                await cur.execute("""UPDATE public."Hours" SET total_time = %s WHERE user_id = %s""", (total_time, user_id,))
            else:
                await cur.execute("""INSERT INTO "Hours" (user_id, total_time) VALUES (%s, %s)""", (user_id, duration,))

            print(f"User {user_id} total time updated: +{duration:.2f}s")

            await conn.commit()

        finally:
            await cur.close()
    

    async def write_user_notif(self, conn, user_id, notif_text):
        cur = conn.cursor()

        id = str(uuid.uuid4())

        try:
            await cur.execute(
                'INSERT INTO "Notifications" VALUES(%s, %s, %s, now(), %s)', (id, user_id, notif_text, False,)
            )

            await conn.commit()

        finally:
            await cur.close()



    async def get_user_notifs(self, conn, user_id) -> list[models.BaseNotifModel]:
        cur = conn.cursor()

        try:
            await cur.execute(
                """
                SELECT "Notifications".id, "Notifications".user_id, "Notifications".text, 
                TO_CHAR(datetime::timestamp, 'DD.MM.YYYY HH24:MI') AS datetime_formatted, 
                "Notifications".read, "Notifications".datetime FROM public."Notifications" WHERE user_id=%s 
                ORDER BY datetime DESC
                """, (user_id,)
            )

            rows = await cur.fetchall()

            if rows == []:
                return None
            
            notifs = []

            for row in rows:

                id, user_id, text, datetime_formatted, read, datetime = row

                notifs.append(models.BaseNotifModel(id=id, user_id=user_id, text=text, datetime=datetime_formatted, read=read))

            return notifs
        
        finally:
            await cur.close()

    
    async def delete_old_notifs(self, conn):
        cur = conn.cursor()

        threshold_date = datetime.now() - timedelta(days=30)

        try:
            await cur.execute(
                'DELETE FROM public."Notifications" WHERE datetime > %s', (threshold_date,)
            )
            
            await conn.commit()
        
        finally:
            await cur.close()



    
    async def update_tsv_user(self, conn, new_username, new_desc, id):
        cur = conn.cursor()

        language = lang_detect(new_desc)

        try:
            await cur.execute(
                
                """
                UPDATE public."User"
                SET tsv=to_tsvector(%s, coalesce(%s, '') || ' ' || coalesce(%s, '')), language=%s
                WHERE id=%s
                """, (language, new_username, new_desc, language, id,)
            )
            
            await conn.commit()
        
        finally:
            await cur.close()




    async def update_tsv_threads(self, conn, new_name, new_desc, tag):
        cur = conn.cursor()

        language = lang_detect(new_desc)

        try:
            await cur.execute(
                
                """
                UPDATE public."Thread"
                SET tsv=to_tsvector(%s, coalesce(%s, '') || ' ' || coalesce(%s, '') || ' ' || coalesce(%s, '')), language=%s
                WHERE tag=%s
                """, (language, new_name, new_desc, tag, language, tag,)
            )
            
            await conn.commit()
        
        finally:
            await cur.close()



    async def search_all(self, conn, query: str):
        cur = conn.cursor()

        try:

            await cur.execute(
                """
                SELECT 'post' AS search_type, "Post".id AS id, "Post".title AS name, "Post".description AS desciption, 
                "User".avatar AS avatar, "Post".location_str AS location_status, "Post".language AS language, "Post".tsv AS tsv
                FROM public."Post"
                LEFT JOIN public."User"
                ON "Post".author_id="User".id
                WHERE "Post".tsv @@ plainto_tsquery("Post".language::regconfig, %s)

                UNION ALL

                SELECT 'user' AS search_type, "User".id AS id, "User".username AS name, "User".description AS desciption, 
                "User".avatar AS avatar, "User".status AS location_status, "User".language AS language, "User".tsv AS tsv
                FROM public."User"
                WHERE "User".tsv @@ plainto_tsquery("User".language::regconfig, %s)

                UNION ALL
    
                SELECT 'thread' AS search_type, "Thread".id AS id, "Thread".name AS name, "Thread".description AS desciption, 
                "Thread".avatar AS avatar, "Thread".tag AS location_status, "Thread".language AS language, "Thread".tsv AS tsv 
                FROM public."Thread"
                WHERE "Thread".tsv @@ plainto_tsquery("Thread".language::regconfig, %s)

                LIMIT 20
                """, (query, query, query,)
            )


            rows_post = await cur.fetchall()

            results = []

            for row in rows_post:
                search_type, id, name, desc, avatar, location_status, language, tsv = row

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"

                desc = desc[:98] + "..."  
                results.append(models.SearchResultModel(
                    search_type=search_type,
                    id=id,
                    name=name,
                    desc=desc,
                    avatar=avatar,
                    location_status=location_status
                ))


            return results
        
        finally:
            await cur.close()

    

    async def search_posts(self, conn, query: str):
        cur = conn.cursor()

        try:

            await cur.execute(
                """
                SELECT 'post' AS search_type, "Post".id AS id, "Post".title AS name, "Post".description AS desciption, 
                "User".avatar AS avatar, "Post".location_str AS location_status, "Post".language AS language, "Post".tsv AS tsv
                FROM public."Post"
                LEFT JOIN public."User"
                ON "Post".author_id="User".id
                WHERE "Post".tsv @@ plainto_tsquery("Post".language::regconfig, %s)

                LIMIT 20
                """, (query,)
            )

            rows_post = await cur.fetchall()

            results = []

            for row in rows_post:
                search_type, id, name, desc, avatar, location_status, language, tsv = row

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"

                desc = desc[:98] + "..."  
                results.append(models.SearchResultModel(
                    search_type=search_type,
                    id=id,
                    name=name,
                    desc=desc,
                    avatar=avatar,
                    location_status=location_status
                ))


            return results
        
        finally:
            await cur.close()

    
    async def search_users(self, conn, query: str):
        cur = conn.cursor()

        try:

            await cur.execute(
                """
                SELECT 'user' AS search_type, "User".id AS id, "User".username AS name, "User".description AS desciption, 
                "User".avatar AS avatar, "User".status AS location_status, "User".language AS language, "User".tsv AS tsv
                FROM public."User"
                WHERE "User".tsv @@ plainto_tsquery("User".language::regconfig, %s)

                LIMIT 20
                """, (query,)
            )


            rows_post = await cur.fetchall()

            results = []

            for row in rows_post:
                search_type, id, name, desc, avatar, location_status, language, tsv = row

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"

                desc = desc[:98] + "..."  
                results.append(models.SearchResultModel(
                    search_type=search_type,
                    id=id,
                    name=name,
                    desc=desc,
                    avatar=avatar,
                    location_status=location_status
                ))


            return results
        
        finally:
            await cur.close()
        
    
    async def search_threads(self, conn, query: str):
        cur = conn.cursor()

        try:

            await cur.execute(
                """
                SELECT 'thread' AS search_type, "Thread".id AS id, "Thread".name AS name, "Thread".description AS desciption, 
                "Thread".avatar AS avatar, "Thread".tag AS location_status, "Thread".language AS language, "Thread".tsv AS tsv 
                FROM public."Thread"
                WHERE "Thread".tsv @@ plainto_tsquery("Thread".language::regconfig, %s)

                LIMIT 20
                """, (query,)
            )


            rows_post = await cur.fetchall()

            results = []

            for row in rows_post:
                search_type, id, name, desc, avatar, location_status, language, tsv = row

                if avatar == "":
                    avatar = "/static/images/profile-pic.png"

                desc = desc[:98] + "..."  
                results.append(models.SearchResultModel(
                    search_type=search_type,
                    id=id,
                    name=name,
                    desc=desc,
                    avatar=avatar,
                    location_status=location_status
                ))


            return results
        
        finally:
            await cur.close()
    

    async def delete_post(self, conn, user_id: str, post_id: str):
        cur = conn.cursor()
        try:
            await cur.execute(
                """
                SELECT "Post".id FROM public."Post"
                WHERE "Post".author_id=%s AND "Post".id=%s
                """, (user_id, post_id,)
            )
            
            if_author = await cur.fetchone()

            if if_author:
                await cur.execute(
                    """DELETE FROM public."Post" WHERE id=%s""", (post_id,)
                )

            else:
                return "not enough rights"
            
            await conn.commit()

        finally:
            await cur.close()