#!/usr/bin/env python

import os, subprocess, random, sys, time
import tweepy, dotenv

scriptpath = os.path.dirname(os.path.abspath(__file__))

# load the keys and secrets from the .env file
dotenv.load_dotenv(os.path.join(scriptpath, '.env'))

CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('BEARER_TOKEN')

client = tweepy.Client(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    bearer_token=BEARER_TOKEN
)

auth = tweepy.OAuth1UserHandler(
    CONSUMER_KEY, CONSUMER_SECRET,
    ACCESS_TOKEN, ACCESS_TOKEN_SECRET
)
api = tweepy.API(auth)

try:
    api.verify_credentials()
    print("Authentication OK")
except Exception as e:
    print("Error during authentication:", e)
    sys.exit(1)

video_dir = os.path.join(scriptpath, "videos")
tmpimg = os.path.join(scriptpath, "tmpimg.jpg")
tmpvid = os.path.join(scriptpath, "tmpvid.mp4")

max_attempts = 10

def getVideo():
    video_file = random.choice([f for f in os.listdir(video_dir) if f.lower().endswith((".mp4", ".mov", ".mkv"))])
    return os.path.join(video_dir, video_file), os.path.splitext(video_file)[0]

def getDuration(video_path):
    cmd = [
        "ffprobe", "-i", video_path,
        "-show_entries", "format=duration",
        "-v", "quiet",
        "-of", "csv=p=0"
    ]
    return float(subprocess.check_output(cmd).decode().strip())

def getRandomScreenshot(video_path, duration):
    screenshot_time = random.uniform(0, duration)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(screenshot_time),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        tmpimg
    ]
    subprocess.check_output(cmd)
    return tmpimg

def getRandomVideoClip(video_path, duration, clipLength):
    start_time = random.uniform(0, max(0, duration - clipLength))
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", video_path,
        "-t", str(clipLength),
        "-c", "copy",
        tmpvid
    ]
    subprocess.check_output(cmd)
    return tmpvid

timer = 1800.0
maxTimer = 1800.0
current_attempts = 0

while True:
    timer += 1.0
    if timer >= maxTimer:
        timer = 0.0
        video_path, video_name = getVideo()
        duration = getDuration(video_path)

        while True:
            try:
                if random.randint(0, 1) == 0:
                    media_file = getRandomScreenshot(video_path, duration)
                    media_id = api.media_upload(media_file).media_id
                else:
                    media_file = getRandomVideoClip(video_path, duration, random.uniform(5, 15))
                    media_id = api.media_upload(media_file, media_category='tweet_video').media_id

                client.create_tweet(
                    text=video_name,
                    media_ids=[media_id]
                )
                break
            except Exception as e:
                print("Error:", e)
                current_attempts += 1
                print(f"Attempt {current_attempts}/{max_attempts}")
                if current_attempts >= max_attempts:
                    print("Max attempts reached. Skipping this tweet.")
                    break

        current_attempts = 0
        if os.path.exists(media_file):
            os.remove(media_file)

    time.sleep(1)
