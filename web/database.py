import pymongo
from bson.objectid import ObjectId
from gridfs import GridFS
import os, sys

class Database():
    def __init__(self):
        # Create the connection
        connection = pymongo.MongoClient('localhost')

        # Connect to Databases.
        voldb = connection['voldb']
        voldbfs = connection['voldbfs']

        # Get Collections
        self.vol_sessions = voldb.sessions
        self.vol_comments = voldb.comments
        self.vol_plugins = voldb.plugins
        self.vol_datastore = voldb.datastore
        self.vol_files = GridFS(voldbfs)

        # Indexes
        self.vol_comments.create_index([('freetext', 'text')])

        self.vol_plugins.create_index([('$**', 'text')])

    ##
    # Sessions
    ##
    def get_allsessions(self):
        sessions = self.vol_sessions.find()
        return [x for x in sessions]

    def get_session(self, sess_id):
        session = self.vol_sessions.find_one({'_id': sess_id})
        return session

    def create_session(self, sess_data):
        sess_id = self.vol_sessions.insert_one(sess_data).inserted_id
        return sess_id

    def update_session(self, sess_id, new_values):
        self.vol_sessions.update_one({'_id':sess_id},{"$set": new_values })
        return True

    ##
    # Comments
    ##
    def get_commentbyid(self, comment_id):
        comment = self.vol_comments.find({'_id': comment_id})
        return comment

    def get_commentbysession(self,session_id):
        comments = self.vol_comments.find({'session_id': session_id}).sort("date_added", -1)
        return [row for row in comments]

    def create_comment(self, comment_data):
        comment_id = self.vol_comments.insert_one(comment_data).inserted_id
        return comment_id

    def search_comments(self, search_text, session_id=None):
        results = []
        rows = self.vol_comments.find({"$text": {"$search": search_text}})
        for row in rows:
            if session_id:
                if row['session_id'] == session_id:
                    results.append(row)
            else:
                results.append(row)
        return results
        
    def delete_comment(self, comment_id):
		self.vol_comments.remove({'_id': comment_id})

    ##
    # Plugins
    ##

    def get_pluginbysession(self, session_id):
        result_rows = []
        plugin_output = self.vol_plugins.find({'session_id': session_id}).sort("created", -1)
        for row in plugin_output:
            result_rows.append(row)
        result_rows = sorted(result_rows)
        return result_rows

    def get_pluginbyid(self, plugin_id):
        plugin_output = self.vol_plugins.find_one({'_id': plugin_id})
        return plugin_output
        
    #PARA EL MENU!!!!    
    def get_pluginby_session_and_name(self, session_id, plugin_name):
        plugin_output ={}
        plugin_list_by_session = self.vol_plugins.find({'session_id': session_id})
        for row in plugin_list_by_session:
            if row['plugin_name'] == plugin_name:
				plugin_output = row
        return plugin_output


    def create_plugin(self, plugin_data):
        plugin_id = self.vol_plugins.insert_one(plugin_data).inserted_id
        return plugin_id

    def search_plugins(self, search_text, session_id=None):
        results = []
        rows = self.vol_plugins.find({"$text": {"$search": search_text}})
        for row in rows:
            if session_id:
                if row['session_id'] == session_id:
                    results.append(row)
            else:
                results.append(row)
        return results

    def update_plugin(self, plugin_id, new_values):
        self.vol_plugins.update_one({'_id':plugin_id},{"$set": new_values })
        return True


    ##
    # File System
    ##
    def get_filebyid(self, file_id):
        file_object = self.vol_files.get(file_id)
        return file_object

    def list_files(self, sess_id):
        results = self.vol_files.find({'session_id': sess_id})
        return results

    def create_file(self, file_data, sess_id, sha256, filename, pid=None, file_meta=None):
        file_id = self.vol_files.put(file_data, filename=filename, sess_id=sess_id, sha256=sha256, pid=pid)
        return file_id


    ##
    # DataStore
    ##

    def get_alldatastore(self):
        results = self.vol_datastore.find()
        return [row for row in results]

    def search_datastore(self, search_query):
        results = self.vol_datastore.find(search_query)
        return [row for row in results]

    def create_datastore(self, store_data):
        data_id = self.vol_datastore.insert_one(store_data).inserted_id
        return data_id

    def update_datastore(self, search_query, new_values):
        self.vol_datastore.update_one(search_query, {"$set": new_values})
        return True


    ##
    # Drop Session
    ##
    def drop_session(self, session_id):
       
        # Drop dump image
        session = self.vol_sessions.find_one({'_id': session_id})
        path_session = session['session_path']
        os.remove(path_session)
        # Drop Plugins
        self.vol_plugins.delete_many({'session_id': session_id})
        # Drop Files
        results = self.vol_files.find({'session_id': session_id})
        for row in results:
            self.vol_files.delete(row['file_id'])
        # Drop DataStore
        self.vol_datastore.delete_many({'session_id': session_id})
        # Drop Notes
        self.vol_comments.delete_many({'session_id': session_id})
        # Drop session
        self.vol_sessions.delete_many({'_id': session_id})
        
        
        
