import os
import io
from PIL import Image, ImageDraw, ImageFont
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import cv2
import re
import g4f
import random 
import string 
import concurrent.futures
from PIL import Image
from easygoogletranslate import EasyGoogleTranslate
from Extras.DeleteStableAPIAccount import DeleteStableAPIAccount

# These 3 lines are required for pymongo to work
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']
from pymongo import MongoClient

class GenerateComic:
    def __init__(self, MONGODB_URI, update_state=None, lang_code="en"):
        self.MONGODB_URI     = MONGODB_URI
        self.STABILITY_KEY   = ""
        self.update_state = update_state
        self.lang_code = lang_code

        client = MongoClient(os.environ.get('MONGODB_URI', self.MONGODB_URI))
        self.db = client.get_database()
        self.generated_images_paths = {}
        self.translator = EasyGoogleTranslate(
            source_language="en",
            target_language=self.lang_code,
            timeout=10
        )

    def printer(self, text):
        if self.update_state != None:
            self.update_state(state='PROGRESS', meta={'progress': text})
            print(text)
        else:
            print(text)

    def lang_translate(self, text):
        if self.lang_code == "en":
            return text 
        else:
            return self.translator.translate(text)

    def convert_text_to_conversation(self, text):
        try:
            response = g4f.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": text}])
            print(response)
            speech, person = self.generate_map_from_text(response)
            # print("Speech: ", speech)
            # print("Person: ", person)

            self.printer(f"[+] Translating dialogues into {self.lang_code} ...")
            final_speech = {}
            for key, value in speech.items():
                final_speech[key] = self.lang_translate(value)

            # print("Final Speech: ", final_speech)

            return (final_speech, person)
        except Exception as e:
            print("Error: ", e)

    def generate_map_from_text(self, text):
        try:
            d = {}
            who_spoke = {}
            dialogue = []
            speak = []

            l = text.split("\n")

            for word in l:
                i = 0
                if 'Scene' not in word and 'Act' not in word:
                    if ':' in word:
                        dialogue.append((word.split(':')[1]))
                        speak.append((word.split(':')[0]))

                for i in range(len(dialogue)):
                    d[i] = dialogue[i]
                    who_spoke[i] = speak[i]

            return (d, who_spoke)
        except Exception as e:
            raise Exception(f"Error occurred during map generation: {e}")
        
    def set_stable_diff_api(self, images_length):
        api_collection = self.db.api
        api_data = api_collection.find_one()
        if api_data['count'] > images_length:
            self.STABILITY_KEY = api_data['api']
            print("[+] Stable API: ", api_data['api'])
            api_collection.update_one({'api': api_data['api']}, {"$set": {'count': api_data['count']-images_length}})
        else:
            
            api_collection.delete_one({'api': api_data['api']})
            self.set_stable_diff_api(images_length)

    def delete_stable_diff_api(self, api_key, email_addr=None, password=None):
        api_collection = self.db.api 
        if email_addr and password:
            api_data   = api_collection.find_one({"api": api_key})
            email_addr = api_data["email"]
            password   = api_data["password"] 
        
        delete_account = DeleteStableAPIAccount()
        delete_account.start(email_addr, password)
        api_collection.delete_one({'api': api_key}) 

    def generate_prompt_for_img_generation(self, comic_name, person, speech, character_list, user_input):
        try:
            prompt = f'Write a detailed prompt for generating a {comic_name} style comic scene where "{person}" says this speech: "{speech}", following are the characters: {character_list}, prompt should be of 60 words (max) which I can use to generate a image using stable diffusion. This speech is on "{user_input}" topic'
            response = g4f.ChatCompletion.create(model="airoboros-70b", messages=[{"role": "user", "content": prompt}])
            # response = g4f.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
            return response
        except:
            return f"""
                Create a {comic_name} style comic scene where "{person}" says, "{speech}".
                Capture the expressions of the user from the dialogue.
                """

    def stable_diff(self, image_prompt, image_name, cfg, step):
        stability_api = client.StabilityInference(
            key=self.STABILITY_KEY,
            verbose=True,
            engine="stable-diffusion-xl-beta-v2-2-2",
        )
        try:
            answer = stability_api.generate(
                prompt=image_prompt,
                seed=992446758,
                steps=int(step),
                cfg_scale=int(cfg),
                width=512,
                height=512,
                samples=1,
                sampler=generation.SAMPLER_K_DPMPP_2M
            )
            folder_path = "static/img/comic"

            for resp in answer:
                for artifact in resp.artifacts:
                    if artifact.finish_reason == generation.FILTER:
                        raise Exception(
                            "Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again")

                    if artifact.type == generation.ARTIFACT_IMAGE:
                        image_path = f"{folder_path}/{image_name}.png"
                        img_binary = io.BytesIO(artifact.binary)
                        img = Image.open(img_binary)
                        img.save(image_path)
                        return image_path
        except Exception as e:
            error_message = str(e)
            balance_err = "Your organization does not have enough balance to request this action"
            details_match = re.search('details = "(.*?)"', error_message)
            if details_match:
                details = details_match.group(1)
                if details.startswith(balance_err):
                    self.delete_stable_diff_api(self.STABILITY_KEY) 
                    raise Exception("Insufficient balance in stable diffusion key. Please top up and try again.")
                error_message = details
            else:
                error_message = error_message
            print(error_message)
            raise Exception(error_message)

    def convert_images_to_pdf(self, images, output_path):
        try:
            images = [
                Image.open(f)
                for f in images
            ]

            images[0].save(
                output_path, "PDF" ,resolution=100.0, save_all=True, append_images=images[1:]
            )
        except Exception as e:
            raise Exception(f"Error occurred during image to PDF conversion: {e}")
 
    def add_line_breaks(self, text):
        try:
            # Split the text into a list of words
            words = text.split()
            new_text = ''
            for i, word in enumerate(words):
                new_text += word
                if (i+1) % 7 == 0:
                    new_text += '\n'
                else:
                    new_text += ' '

            return new_text
        except AttributeError as e:
            raise Exception(f"Error occurred during line break addition: {e}")

    def add_text_to_image(self, image_path, text_from_prompt, image_name):
        try:
            image = Image.open(image_path)
            right_pad = 0
            left_pad = 0
            top_pad = 50
            bottom_pad = 0
            width, height = image.size

            new_width = width + right_pad + left_pad
            new_height = height + top_pad + bottom_pad

            result = Image.new(image.mode, (new_width, new_height), (255, 255, 255))
            result.paste(image, (left_pad, top_pad))

            font_type = ImageFont.truetype("static/font/animeace2_reg.ttf", 12)

            draw = ImageDraw.Draw(result)
            draw.text((10, 0), text_from_prompt, fill='black', font=font_type)
            result.save(f"static/img/comic/{image_name}.png")
            border_img = cv2.imread(f"static/img/comic/{image_name}.png")

            borderoutput = cv2.copyMakeBorder(
                border_img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[0, 0, 0])

            cv2.imwrite(f"static/img/comic/{image_name}.png", borderoutput)
        except Exception as e:  
            raise Exception(f"Error occurred during text addition: {e}")

    def generate_random_alpha_string(self, length):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string
    
    def process_comic_page(self, index, response1, response2, customisation, cfg, step, character_list, user_input):
        try:
            image_name = self.generate_random_alpha_string(10)
            image_prompt = self.generate_prompt_for_img_generation(customisation, response1, response2, character_list, user_input)
            image_path = self.stable_diff(image_prompt, image_name, cfg, step) 
            print(image_path)
            self.generated_images_paths[index] = image_path

            text = self.add_line_breaks(response2)
            self.add_text_to_image(f"static/img/comic/{image_name}.png", text, image_name)
        except Exception as e:
            print("Error [process_comic_page()]: ", e)

    def start(self, user_input, customisation, cfg, step, output_path):
        # return [
        #         'static/img/comic/1.png',    
        #         'static/img/comic/2.png',   
        #         'static/img/comic/3.png',   
        #         'static/img/comic/4.png',   
        #         'static/img/comic/5.png',   
        #         'static/img/comic/6.png',   
        #         'static/img/comic/7.png',   
        #         'static/img/comic/8.png', 
        #         'static/img/comic/9.png',   
        #         'static/img/comic/10.png',   
        #         'static/img/comic/11.png',  
        #         'static/img/comic/12.png',   
        #         'static/img/comic/13.png',   
        #         'static/img/comic/14.png',
        #         'static/img/comic/15.png'          
        #     ]
        try: 
            self.printer("[-] Generating Comic Content ...")
            prompt = "Convert the following boring text into a comic style conversation between characters while retaining information. Try to keep the characters as people from the story. Make 6 scenes comic. Keep a line break after each dialogue and don't include words like Scene 1, narration context and scenes etc. Keep the name of the character and not character number: \n\n\n"
            input = prompt + user_input
            response = self.convert_text_to_conversation(input)
            self.printer(response)
            self.printer("[+] Generated Successfully")

            # self.printer("[-] Fetching Fresh Stable API ...")
            total_scenes = len(response[0]) 
            self.set_stable_diff_api(total_scenes)
            # self.printer("[+] Fetched Successfully")

            self.printer("[-] Generating Comic Poster ...")
            try:
                comic_poster_image_prompt = g4f.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": f"Generate a prompt for a {customisation} like comic poster on the topic: '{user_input}'"}])
            except Exception as e:
                comic_poster_image_prompt = f"Generate a {customisation} like comic poster on the topic: '{user_input}'"
            image_name = self.generate_random_alpha_string(10)
            image_path = self.stable_diff(comic_poster_image_prompt, image_name, cfg, step) 
            self.generated_images_paths[0] = image_path 
            self.printer("[+] Generated Successfully")

            self.printer("[-] Generating Comic Scenes ...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []
                for i in range(total_scenes):
                    index = i+1
                    future = executor.submit(self.process_comic_page, index, response[1][i], response[0][i], customisation, cfg, step, response[1], user_input)
                    futures.append(future)
                concurrent.futures.wait(futures)
            self.printer("[+] Comic Scenes Generated Successfully")

            self.printer("[-] Generating PDF Comic ...")
            generated_images_paths_new = dict(sorted(self.generated_images_paths.items()))
            generated_images_paths = list(generated_images_paths_new.values())
            self.convert_images_to_pdf(generated_images_paths, output_path)  
            self.printer("[+] Comic Generated Successfully!")
            return generated_images_paths
        except Exception as e:
            self.printer(f"Error: {e}")
            return f"Error: {e}"
    
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    MONGODB_URI          = os.environ.get('MONGODB_URI') 
    test =  GenerateComic(MONGODB_URI, lang_code="hi")

    user_input = "Crime patrol"  
    customisation = "disney" # Enter your favourite comic style like DC, Marvel, Anime or get creative!
    cfg = 8   # 0-10      
    step = 30 # 0-100     
    output_path     = f"static/pdfs/{user_input[:30].lower().replace(' ', '_').replace('-', '_')}.pdf"
    test.start(user_input, customisation, cfg, step, output_path)

    # prompt = "Convert the following boring text into a comic style conversation between characters while retaining information. Try to keep the characters as people from the story. Make 6 scenes comic. Keep a line break after each dialogue and don't include words like Scene 1, narration context and scenes etc. Keep the name of the character and not character number: \n\n\n"
    # input = prompt + user_input
    # test.convert_text_to_conversation(input)
