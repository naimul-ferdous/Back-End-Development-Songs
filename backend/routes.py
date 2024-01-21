from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    """return length of documents"""
    count = db.songs.count_documents({})
    return {"count": count}, 200


@app.route("/song", methods=["GET"])
def songs():
    data= db.songs.find({})
    if data:
        return json_util.dumps({"songs":list(data)}), 200

    return {"message": "Internal server error"}, 500


@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    song= db.songs.find_one({"id": id})
    if song:
        return json_util.dumps(song), 200
    return {"message": f"song with {id} not found"}, 404


@app.route("/song", methods=["POST"])
def create_song():
    body= request.json
    id= body["id"];
    song= db.songs.find_one({"id": id})

    if song:
        return jsonify({"Message":f"song with id {id} already present"}), 302
    
    insert_result= db.songs.insert_one(body)

    return json_util.dumps({"inserted id": insert_result.inserted_id}), 201
    

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    body= request.json
    song= db.songs.find_one({"id": id})

    if song:
        # db.songs.update_one(body)

        # Define a query to find the document you want to update
        query = {"id": id}

        # Define the update that you want to apply
        update = {"$set": body}

        # Update the first document matching the query
        update_result = db.songs.update_one(query, update)

        # Check if the update was successful
        if update_result.modified_count > 0:
            # Fetch the updated document
            updated_document = db.songs.find_one(query)
            # print("Updated document:", updated_document)
            return json_util.dumps(updated_document), 200
        else:
            return jsonify({"message":"song found, but nothing updated"}), 200


        
    
    return jsonify({"message":"song not found"}), 404


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    # Delete the first document matching the query
    delete_result = db.songs.delete_one({"id": id})

    # Check if the delete was successful
    if delete_result.deleted_count > 0:
        return jsonify(f'Documents deleted: {delete_result.deleted_count}'), 204
    else:
        return jsonify({"message":"song not found"}), 404