from groq import Groq
#import instagrapi
from InstagramReelDownloader import ReelDownload
import fastapi
import os
import moviepy as mp
import instaloader
import json
import base64

app = fastapi.FastAPI()

def download_reel(url:str):
	''' 
	function to start it all donwloads the media from instagram and then collects it and send it to the post_to_text(video,text) function for extraction of data
	'''
	print('Downloading Post')
	L = instaloader.Instaloader()
	reel_shortcode = url.split('/')[-2]
	post = instaloader.Post.from_shortcode(L.context, reel_shortcode)
	L.download_post(post,target="Video")
	os.chdir('Video')
	for i in os.listdir():
		print(i)
		if i.endswith('mp4') or i.endswith('jpg'):
			video = i
		if i.endswith('txt'):text = open(i,'r').read()
	text = post_to_text(video,text)
	print(os.getcwd())
	if 'Videos' not in os.listdir():os.mkdir('Videos')
	if 'Videos' in os.getcwd().split('/'):
		for i in os.listdir():
			print(i)
			os.remove(i)
	if "Videos" not in os.listdir():
		os.chdir('..')
	return text

def encode_image(img):
	'''
	encode the image in base64
	'''
	with open(img, "rb") as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')

def audio_extraction(video):
	'''
	an attempt to extract the audio and to see if it exsists or not in the video and if so then saves it as audio.wav so it can be collected by the llm in the post_to_text(video,text) function
	'''
	try:
		vid = mp.VideoFileClip(video)
		if vid.audio:
			vid.audio.write_audiofile("audio.wav")
			return True
		else:
			return False
	except:
		return False

def post_to_text(video,text):
	'''
	function where we use llms and computer vision to extract data from images or audio (extracted from video that will be converted into text) to make json data 	and send it back
	'''
	Client = Groq(api_key="")
	
	is_video = audio_extraction(video)
	print('video to mp')
	if is_video:
		print('extracting audio')
		print('extracting audio completly')
		with open("audio.wav", "rb") as file:
			translation = Client.audio.transcriptions.create(
		      file=file,
		      model="whisper-large-v3-turbo",
		      prompt="Collect the Restaurent Name , Offer , Special Food And All OTher Important Data Related To The Food And Offer Provided And Give Output in Json Format",
		      response_format="json",
		      language="en")
		print(text)
		print(translation.text)
		to_json = Client.chat.completions.create(
		messages=[{"role":"system","content":"Your Convert Raw Text data Into Json and only return the json nothing else just the json data and if you can return anything just say nothing"},{"role":"user","content":f"here is the raw text from a short form content to be converted into json collect infomration like name , offer what they provide and where it is {translation.text} and here is the description about the short form content for accuracy {text} i want the name of restatuernt , product name , price a small Description and location and from which social media u got it from and here is the url from where i got it from  {url}"}],model="llama-3.1-8b-instant",temperature=0.3,stop=None,stream=False)
		try:
			return json.loads(to_json.choices[0].message.content)
		except json.decoder.JSONDecodeError:
			return None
	else:
		to_json = Client.chat.completions.create(messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"What is in this image im visually impared please give th"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encode_image(video)}",
                    },
                },
            ],
        }
    ],
    model="llama-3.2-11b-vision-preview",temperature=0.3,stop=None,stream=False
)


	print(to_json.choices[0].message.content)
	try:
		return json.loads(to_json.choices[0].message.content)
	except json.decoder.JSONDecodeError:
		return None

#print(download_reel("https://www.instagram.com/p/DHGUvjNIZuq/"))

@app.post("/extract_reel_data/")
async def extract_reel_data(url: str):
	'''
	fastapi to send and recive data
	'''
	return download_reel(url)
