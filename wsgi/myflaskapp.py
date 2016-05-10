from gevent import monkey
monkey.patch_all()
import time
from threading import Thread
import os
from flask import Flask
from flask import request
import pymongo
import json
from bson import json_util
from bson import objectid
import re
from datetime import datetime
from flask.ext.cors import CORS
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, \
    close_room, disconnect
from bson.objectid import ObjectId
app = Flask(__name__)
CORS(app, resources=r'/*', allow_headers='Content-Type')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None
#add this so that flask doesn't swallow error messages
app.config['PROPAGATE_EXCEPTIONS'] = True
#os.environ['OPENSHIFT_MONGODB_DB_URL']='mongodb://pythontest:pythontest@127.0.0.1:27017/'

#a base urls that returns all the parks in the collection (of course in the future we would implement paging)
@app.route('/')
def root():
    return app.send_static_file('index.html')
@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

@app.route("/api/series")
def series():
    #setup the connection
    print "hola"
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    start = datetime.now()
    end = datetime(2100, 5, 1)
    #query the DB for all the parkpoints
    result = db.serie.find()
    series=[]
    for serie in result:
        episode = db.episode.find({'serie_id': serie['_id'],"firstAired": {"$gte": start, "$lt": end}}).sort("firstAired", 1).limit(1)
        if episode.count()==0:
            serie['finished']=True
        else:
            serie['finished']=False
        series.append(serie)
    print series
    #Now turn the results into valid JSON
    return str(json.dumps({'results':list(series)},default=json_util.default))

@app.route("/api/seriesCarousel")
def seriesCarousel():
    #setup the connection
    print "Carousel"
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    #query the DB for all the parkpoints
    result = db.serie.find().limit(10)
    series=[]
    for serie in result:
        tmp={}
        tmp['id']=serie['id']
        tmp['name']=serie['name']
        tmp['banner']=serie['banner']
        series.append(tmp)
    print series
    #Now turn the results into valid JSON
    return str(json.dumps({'results':list(series)},default=json_util.default))
@app.route("/api/series/<serieId>")
def serie(serieId):
    #setup the connection
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]

    #query the DB for all the parkpoints
    result = db.serie.find({'id': serieId})
    #Now turn the results into valid JSON
    return str(json.dumps({'results':list(result)},default=json_util.default))
#return a specific park given it's mongo _id
@app.route("/api/episodes/<serieId>")
def episodes(serieId):
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    serie = db.serie.find({'id': serieId})
    print serie[0]['_id']
    result = db.episode.find({'serie_id': serie[0]['_id']})
    return str(json.dumps({'results' : list(result)},default=json_util.default))

@app.route("/api/episode/<episodeId>")
def episode(episodeId):
    print "bien"
    print episodeId
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    episode = db.episode.find({'_id': ObjectId(episodeId)})
    return str(json.dumps(episode[0],default=json_util.default))

@app.route("/api/nextEpisode/<serieId>")
def nextEpisode(serieId):
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    start = datetime.now()
    end = datetime(2100, 5, 1)
    serie = db.serie.find({'id': serieId})
    result = db.episode.find({'serie_id': serie[0]['_id'],"firstAired": {"$gte": start, "$lt": end}}).sort("firstAired", 1).limit(1)
    return str(json.dumps({'results' : list(result)},default=json_util.default))
@app.route("/api/addFavoriteSerie", methods=['POST'])
def addFavoriteSerie():
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    data = json.loads(request.data)
    serie_id=data['serie_id']
    user_id=data['user_id']
    user=db.user.find({"id":user_id})
    serie=db.serie.find({"id":serie_id})
    if(user.count()==0):
        return "User does not exist"
    else:
        if serie.count()==0:
            return "The providen serie id does no exist"    
        else:
            user=user[0]
            serie=serie[0]
            print user
            print serie
            series_list=user['series']
            series_list.append(serie_id)
            user['series']=series_list
            db.user.save(user)
            users_list=serie['favorited_by']
            users_list.append(user_id)
            serie['favorited_by']=users_list
            print users_list
            print series_list
            print user['series']
            print serie['favorited_by']
            db.serie.save(serie)
            serie=db.serie.find({"id":serie_id})
            print serie[0]
            return "Serie added to favorites"
@app.route("/api/removeFavoriteSerie", methods=['POST'])
def removeFavoriteSerie():
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    data = json.loads(request.data)
    serie_id=data['serie_id']
    user_id=data['user_id']
    print user_id
    print serie_id
    user=db.user.find({"id":user_id})
    serie=db.serie.find({"id":serie_id})
    if(user.count()==0):
        return "User does not exist"
    else:
        if serie.count()==0:
            return "The providen serie id does no exist"    
        else:
            user=user[0]
            serie=serie[0]
            if serie_id in user['series']:
                user['series'].remove(serie_id)
                print user['series']
            db.user.save(user)
            if user_id in serie['favorited_by']:
                serie['favorited_by'].remove(user_id)
                print serie
            print serie
            db.serie.save(serie)
            return "Serie removed from favorites"
@app.route("/api/registerCalendar", methods=['POST'])
def registerCalendar():
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    data = json.loads(request.data)
    user_id=data['userID']
    calendar_id=data['calendarID']
    print user_id
    print calendar_id
    user=db.user.find({"id":user_id})
    if(user.count()==0):
        return "User does not exist"
    else:
        user=user[0]
        user['calendarID']=calendar_id
        print user['calendarID']
        db.user.save(user)
        return "User's calendar updated"
@app.route("/api/removeCalendar", methods=['POST'])
def removeCalendar():
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    data = json.loads(request.data)
    user_id=data['userID']
    print user_id
    user=db.user.find({"id":user_id})
    if(user.count()==0):
        return "User does not exist"
    else:
        user=user[0]
        user['calendarID']=-1
        print user['calendarID']
        db.user.save(user)
        return "User's calendar removed"

@app.route("/api/getFavorites/<userId>")
def getFavorites(userId):
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    print userId
    user=db.user.find({"id":userId})
    if user.count()==0 :
        return "User not found"
    else:
        series=[]
        for serie_id in user[0]['series']:
            series.append(db.serie.find_one({"id":serie_id}))
        return str(json.dumps({'results' : list(series)},default=json_util.default))
@app.route("/api/getFavoritesEpisodes/<userId>")
def getFavoriteEpisodes(userId):
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    print userId
    user=db.user.find({"id":userId})
    if user.count()==0 :
        return "User not found"
    else:
        episodes=[]
        for serie_id in user[0]['series']:
            start = datetime.now()
            serie=db.serie.find_one({"id":serie_id})
            print serie['name']
            end = datetime(2100, 5, 1)
            db_episodes = db.episode.find({'serie_id': serie['_id'],"firstAired": {"$gte": start, "$lt": end}}).sort("firstAired", 1)
            for episode in db_episodes:
                print episode
                episode['serie_name']=serie['name']
                episodes.append(episode)
            episodes.extend(list(db_episodes))
            print episodes
        print episodes
        return str(json.dumps({'results' : episodes},default=json_util.default))
@app.route("/api/getTimeForFavorites/<arduino_id>",methods=['GET'])
def getTimeFavorites(arduino_id):
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    print arduino_id
    user=db.user.find({"arduino_id":arduino_id})
    if user.count()==0 :
        return "User not found"
    else:
        series=[]
        s={}
        for serie_id in user[0]['series']:
            start = datetime.now()
            serie=db.serie.find_one({"id":serie_id})
            end = datetime(2100, 5, 1)
            result = db.episode.find({'serie_id': serie['_id'],"firstAired": {"$gte": start, "$lt": end}}).sort("firstAired", 1).limit(1)
            if result.count()!=0:
                #series.append( result[0]['firstAired'])
                s['$date']=1800
                #series.append(s)
                break;
        #return str(json.dumps( list(series),default=json_util.default))
        return str(json.dumps( s,default=json_util.default))
@app.route("/api/registerUser",methods=['POST'])
def registerUser():
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    data = json.loads(request.data)
    user_id=data['user_id']
    print user_id
    print data
    user=db.user.find({"id":user_id})
    message={}
    if user.count()==0 :
        db.user.save({"id":user_id,"series":[],"arduino_id":-1,"calendarID":-1})
        message['message']="200 OK: User successfully registered"
        message['calendarID']=-1
        message['series']=[]
        return str(json.dumps( message,default=json_util.default))
    else:
        message['message']="501 User already registered"
        message['calendarID']=user[0]['calendarID']
        message['series']=user[0]['series']
        return str(json.dumps( message,default=json_util.default))
@app.route("/api/registerArduino/<userId>/<arduinoId>",methods=['GET','POST'])
def registerArduino(userId, arduinoId):
    print "piwqehiuwqhdasjbdasjhdgasjhdgqwdiahsbjdavgdhuqwvdqkbasjasjhgd"
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    user=db.user.find({"id":userId})
    if user.count()==0 :
        return "ERROR: The provided user does not exist"
    else:
        user=user[0]
        user['arduino_id']=arduinoId
        db.user.save(user)
        return "Arduino registered with the provided user"

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    print "Ha empezado"
    while True:
        time.sleep(10)
        count += 1
        print "sended"
        socketio.emit('socket:notification',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')
    
@app.route('/<path:path>')
def static_proxy(path):
  # send_static_file will guess the correct MIME type
  return app.send_static_file(path)
def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    print "Ha empezadoa"
    while True:
        time.sleep(120)
        count += 1
        print "sended"
        series_json=getTimeSeries()
        socketio.emit('socket:notification',
                      series_json,
                      namespace='/test')
def getTimeSeries():
    conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
    db = conn[os.environ['OPENSHIFT_APP_NAME']]
    series=[]
    result=db.serie.find()
    for serie in result:
        s={}
        start = datetime.now()
        end = datetime(2100, 5, 1)
        result = db.episode.find({'serie_id': serie['_id'],"firstAired": {"$gte": start, "$lt": end}}).sort("firstAired", 1).limit(1)
        if result.count()!=0:
            time=result[0]['firstAired']
            print time
            now=datetime.now()
            dif=time-now
            if dif.total_seconds()<24*2*3600:
                print dif
                s['serie_name']=serie['name']
                s['episode_name']=result[0]['episode_name']
                s['dif']=dif.total_seconds()
                s['serie_id']=serie['id']
                s['episode_id']=result[0]['_id']
                series.append(s)
    return json.dumps( list(series),default=json_util.default)

if __name__ == "__main__":
    if thread is None:
        thread = Thread(target=background_thread)
        thread.start()
    socketio.run(app)

