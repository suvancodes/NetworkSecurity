from pymongo import MongoClient



url = "mongodb+srv://suvankarpayra12_db_user:subho123@cluster0.0a2iwac.mongodb.net/?appName=Cluster0"

client = MongoClient(url)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
    