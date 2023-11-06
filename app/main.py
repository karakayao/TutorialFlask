from flask import Flask
from pathlib import Path
from instagrapi import Client
from instagrapi.types import Media
import os
# import my
import random
import datetime
import time
import json
import threading
from decouple import config

app = Flask(__name__)

service_started = False


mainFolder = "downloads"
json_filename = "collectionMedias.json"
json_filename_commented_media = "commentedMedias.json"
json_filename_comments = "comments.json"

waitTime = 60
mediaProcessFlag = False
commentProcessFlag = False

cl = Client()


# @app.route("/start")
# def start():
#     if service_started:
#         return "<p>Server çalışıyor!</p>"
#     else:
#         return "sds"
    
@app.route("/start")
def start():
    if service_started:
        return "<p>Server çalışıyor!</p>"
    else:
        start_service()
        thread = threading.Thread(target=start_loop)
        thread.start()
        return "<p>Server başlatıldı.!</p>"
    
@app.route("/mpflag")
def mpflag():
    if mediaProcessFlag:
        return "<p>mp çalışıyor!</p>"
    else:
        return "<p>mp çalışmıyor!</p>"


def start_service():
    global service_started

    if not os.path.exists(mainFolder):
        os.mkdir(mainFolder)
        print(mainFolder + " klasörü oluşturuldu.")
    else:
        print("klasör zaten var")

    cl.load_settings("session.json")
    # loginSuccess = cl.login(my.username, my.password)
    loginSuccess = cl.login(config('USERNAME'), config('PASSWORD'))
    print(str(loginSuccess))
    # cl.set_locale("tr_TR")
    # cl.set_country_code(90)
    # cl.set_timezone_offset(3 * 3600)
    # cl.dump_settings("session.json")
    # user_id = cl.user_id_from_username(my.username)
    user_id = cl.user_id_from_username(config('USERNAME'))
    print("Login success: " + user_id)  

    if loginSuccess:
        service_started = True  
    

    

def start_loop():
    global waitTime
    global mediaProcessFlag
    global commentProcessFlag

    while True: 
        now = datetime.datetime.now().time()
        
        if (datetime.time(11, 0) <= now <= datetime.time(14, 0)) or (datetime.time(16, 0) <= now <= datetime.time(18, 0)):  #post vakti                                            
            if not mediaProcessFlag:
                print("Upload saati geldi. Rastgele bekleme süresi geçtikten sonra işlem başlatılacak.")
                # waitTime = random.randint(1, 7200)
                print(str(waitTime) + " saniye sonra işlem başlayacak...")
                time.sleep(waitTime)
                process_media()   
                mediaProcessFlag = True   
                print("İşlem tamamlandı.")  
                print("Bir sonraki upload saati bekleniyor...") 
            else:
                time.sleep(waitTime)
        # elif (datetime.time(9, 0) <= now <= datetime.time(11, 0)) or (datetime.time(14, 0) <= now <= datetime.time(16, 0)): #comment vakti
        #     if not commentProcessFlag:
        #         print("Comment saati geldi. Rastgele yorumlar yapılacak.")
        #         process_commment()
        #         print("İşlem tamamlandı.")  
        #         print("Bir sonraki comment saati bekleniyor...") 
        else: #boş zaman
            mediaProcessFlag = False
            waitTime = 60
            time.sleep(waitTime)

#POST ISLEME BOLUMU+++++++++++
def process_media():
        folders = [
            d for d in os.listdir(mainFolder) if os.path.isdir(os.path.join(mainFolder, d))
        ]
        collectionMedias = cl.collection_medias("ALL_MEDIA_AUTO_COLLECTION")
        save_collection_media_pk_to_json(collectionMedias)

        media_pk_to_post = get_media_pk_from_json()

        if not media_pk_to_post == None:
            media = cl.media_info(media_pk_to_post)
            mediaType = ""

            if media.media_type == 1:
                mediaType = "Photo"
            elif media.media_type == 2 and media.product_type == "feed":
                mediaType = "Video"
            elif media.media_type == 2 and media.product_type == "igtv":
                mediaType = "IGTV"
            elif media.media_type == 2 and media.product_type == "clips":
                mediaType = "Reel"
            elif media.media_type == 8:
                mediaType = "Album"

            # print("Media Type: " + mType)
            mediaFolder = os.path.join(mainFolder, media.pk)
            os.mkdir(mediaFolder)
            # print("Klasor olusturuldu: " + mediaFolder)

            with open(
                mediaFolder + "\\caption.txt", "w", encoding="utf-8"
            ) as caption_file:
                caption_file.write(media.caption_text)
                # print("Caption indirildi.")

            caption_text_with_username = (
                "@" + media.user.username + "\r\n\r\n" + media.caption_text
            )

            if mediaType == "Photo":
                path = cl.photo_download(media.pk, mediaFolder)
                fixedPath = str(path)
                if path.suffix == '.webp':
                    fixedPath = str(path).replace(".webp", ".jpg")
                    os.rename(str(path), fixedPath)                
                elif path.suffix == '.heic':
                    fixedPath = str(path).replace(".heic", ".jpg")
                    os.rename(str(path), fixedPath)      
                cl.photo_upload(
                    fixedPath, 
                    caption_text_with_username
                )
                print("Photo upload completed.")
            elif mediaType == "Video":
                cl.video_upload(
                    cl.video_download(media.pk, mediaFolder), caption_text_with_username
                )
                print("Video upload completed.")
            elif mediaType == "IGTV":
                cl.igtv_upload(
                    cl.igtv_download(media.pk, mediaFolder), caption_text_with_username
                )
                print("IGTV upload completed.")
            elif mediaType == "Reel":
                cl.clip_upload(
                    cl.clip_download(media.pk, mediaFolder), caption_text_with_username
                )
                print("Reel upload completed.")
            elif mediaType == "Album":
                paths = cl.album_download(media.pk, mediaFolder)
                fixedPaths = []
                fixedPaths.clear()

                for filePath in paths:
                    if filePath.suffix == ".webp" or filePath.suffix == ".heic":
                        newPath = filePath.with_suffix(".jpg")
                        fixedPaths.append(newPath)                    
                    else:
                        fixedPaths.append(filePath)

                for fileName in os.listdir(paths[0].parent):
                    if fileName.endswith(".webp"):
                        oldPath = os.path.join(paths[0].parent, fileName)
                        newPath = os.path.join(paths[0].parent, fileName.replace(".webp", ".jpg"))
                        os.rename(oldPath, newPath)
                    elif fileName.endswith(".heic"):
                        oldPath = os.path.join(paths[0].parent, fileName)
                        newPath = os.path.join(paths[0].parent, fileName.replace(".heic", ".jpg"))
                        os.rename(oldPath, newPath)    

                cl.album_upload(fixedPaths, caption_text_with_username)
                print("Album upload completed.")

                for index, r in enumerate(media.resources):
                    for p in fixedPaths:
                        if str(r.pk) in str(p):
                            newname = str(p).rsplit(".", 1)
                            newname = f"{newname[0]}_{str(index + 1)}.{newname[1]}"
                            os.rename(str(p), newname)

        mark_posted_media_pk_to_json(media_pk_to_post)
  
def save_collection_media_pk_to_json(collection_medias):
    existing_data = []

    if os.path.exists(json_filename):
        with open(json_filename, 'r') as json_file:
            existing_data = json.load(json_file)

    # Yeni öğeleri JSON verilerine ekleyin (sadece eksik olanlar)
    for media in collection_medias:
        if not any(existing_media["pk"] == media.pk for existing_media in existing_data):
            newItem = {
                "pk": media.pk,
                "posted": False
            }
            existing_data.append(newItem)

    with open(json_filename, 'w') as json_file:
        json.dump(existing_data, json_file)

def get_media_pk_from_json():

    if os.path.exists(json_filename):
        with open(json_filename, 'r') as json_file:
            existing_data = json.load(json_file)

    for m in existing_data:
        if m["posted"] == False:
            return m["pk"]

    return None #bulamazsa None döndürür

def get_all_media_pk_from_json():
    if os.path.exists(json_filename):
        with open(json_filename, 'r') as json_file:
            existing_data = json.load(json_file)

    pkList = []

    for m in existing_data:
        pkList.append(m["pk"])

    return pkList

def mark_posted_media_pk_to_json(mediaPk):
    if os.path.exists(json_filename):
        with open(json_filename, 'r') as json_file:
            existing_data = json.load(json_file)

    for m in existing_data:
        if m["pk"] == mediaPk:
            m["posted"] = True

    with open(json_filename, 'w') as json_file:
        json.dump(existing_data, json_file)
#POST ISLEME BOLUMU-----------
