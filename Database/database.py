# API KEY 9yVa2T2OlmILdgFdNSz2xz5uxxCcgOZn8vX2hoNV

import firebase_admin
from firebase_admin import credentials, firestore

# Use the service account .json file to establish valid credentials to your Firestore database
credential = credentials.Certificate("Database/food_and_fitness_database_service_key.json")
# Use admin privileges to initialize the connection to the database using the credentials
firebase_admin.initialize_app(credential)

# access your Firestore database as a client
db = firestore.client()


# custom class for all methods that pertain to CRUD(Create, Read, Update, Delete) and the database
class Database:
    # initialize each Database object with the path for each sub-collection of items
    def __init__(self, collection_name="", initial_document="", current_date=""):
        # make a reference to all sub-collections which are defined by dates
        if collection_name == "database" and initial_document != "user_weight":
            # create a class variable to reference the sub-collection's path
            self.main_reference = db.collection(f"{collection_name}").document(f"{initial_document}").collection(
                f"{current_date}")
        # make a reference to all collections which don't contain sub-collections for each date
        else:
            # create a class variable to reference the sub-collection's path
            self.main_reference = db.collection(f"{collection_name}")

    # a method specific for retrieving information over a date range (specific for the graphing functionality)
    @staticmethod
    def get_info_for_graphs(document_name, date_range):
        items = {}  # empty dictionary is created to store all items
        # create a reference to ALL sub-collections within the root collection
        collections = db.collection("database").document(f"{document_name}").collections()
        # iterate through all collections
        for collection in collections:
            # if the date of the collection is within the date_range, then retrieve the information
            if collection.id in date_range:
                # create a key in the dictionary based on the date, and add an empty list to it
                items[collection.id] = []
                # loop through all the documents in the sub-collection
                for doc in collection.stream():
                    # add all the item's information, as a dictionary, to the empty list for that date
                    items[collection.id].append(doc.to_dict())

        return items  # return the dictionary (keys = dates, values = list containing dictionaries for each item)

    # a method specific for retrieving information for the users profile (specific for the displaying user profile info)
    @staticmethod
    def get_user_profile_info():
        items = []  # create an empty list for each item
        # reference the user_profile document in the root collection and get all sub-collections
        collections = db.collection("database").document("user_profile").collections()
        # loop through all the collections
        for collection in collections:
            # retrieve all the documents in the sub-collection
            for doc in collection.stream():
                # add all the information on each document to the list
                items.append(doc)

        return items  # return the list with items (each index is a user_profile item - Weight, Height)

    # read all documents and their fields from the main_reference collection
    def get_from_database(self):
        return self.main_reference.stream()  # returns a generator object

    # read all documents and their fields from a specific date collection
    @staticmethod
    def search_specific_date(collection_name, initial_document, specific_date, return_value):
        # create a reference for a specific date, rather than the current date
        specific_date_items = db.collection(f"{collection_name}").document(f"{initial_document}").collection(
                f"{specific_date}").stream()
        # check to see what value needs to be returned
        if return_value == "length":
            return len(list(specific_date_items))  # return length of the list of items
        elif return_value == "items":
            return specific_date_items  # return the items

    # read all documents and their fields that meet the required conditions
    def search(self, field_name, where_cond):
        # return items where the field name is equal to the condition specified
        return self.main_reference.where(f"{field_name}", u"==", f"{where_cond}").stream()

    # add item to database as a document with specified field information
    def add_to_database(self, item_name, item_info):
        # field information is added as a dictionary, making it easy to unpack and use
        self.main_reference.document(f"{item_name}").set(item_info)

    # edit item in database with newly specified field information
    def edit_database(self, edit_item, edit_info):
        # .set() will override any previously inputted information to prevent duplicates
        self.main_reference.document(f"{edit_item}").set(edit_info)

    # delete items in the database (documents only)
    def remove_from_database(self, item_name):
        # use built in delete() method, to prevent the need to delete each field individually
        self.main_reference.document(f"{item_name}").delete()
