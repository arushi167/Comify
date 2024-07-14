# These 3 lines are required for pymongo to work
import dns.resolver
dns.resolver.default_resolver=dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers=['8.8.8.8']
from pymongo import MongoClient
import os 
from dotenv import load_dotenv
load_dotenv()

class AddToDB:
    def __init__(self):
        client = MongoClient(os.environ.get('MONGODB_URI'))
        self.db = client.get_database()

    def start(self, api_key, email, password):
        api_collection = self.db.api 
        api_collection.insert_one({'api': api_key, 'count': 125, 'email': email, 'password': password}) 

if __name__ == '__main__':
    test = AddToDB()
    with open('api.txt') as f:
        for api in f.readlines():
            test.start(api.strip())