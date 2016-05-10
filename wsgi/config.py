import os
import pymongo
import requests
import shutil
from xml.dom import minidom
from datetime import datetime
#setup the connection
API_KEY=""
try: 
	conn = pymongo.Connection(os.environ['OPENSHIFT_MONGODB_DB_URL'])
except Exception : 
	conn = pymongo.Connection("mongodb://pythontest:pythontest@127.0.0.1:27017/pythontest")
db = conn['pythontest']

collection_serie = db['serie']
collection_episode = db['episode']
series=['Fringe','Lost','New Girl','Stargate SG-1','Star Wars Rebels','Modern Family','The Walking Dead','The Big Bang Theory']

for request_serie in series:
	r = requests.get('http://thetvdb.com/api/GetSeries.php?seriesname='+request_serie)
	xml=unicode(r.text)
	xml=xml.encode("utf-8")
	xmldoc = minidom.parseString(xml)
	series_xml = xmldoc.getElementsByTagName('Series') 
	for serie in series_xml:
		id=serie.getElementsByTagName('seriesid')
		id=id[0].firstChild.nodeValue
		name=serie.getElementsByTagName('SeriesName')
		if name[0].firstChild != None:
			name=name[0].firstChild.nodeValue
			if collection_serie.find({"name":name}).count() >0:
				print "Paso"
				break
		else:
			name=''
			pass
		banner=serie.getElementsByTagName('banner')
		if banner[0].firstChild != None:
			banner=banner[0].firstChild.nodeValue
			url="http://thetvdb.com/banners/"+banner
			index=banner.rindex('/')
			banner="static/"+banner[index+1:]
			response = requests.get(url, stream=True)
			with open(banner, 'wb') as out_file:
				shutil.copyfileobj(response.raw, out_file)
			del response	
		else:
			banner=''
		overview=serie.getElementsByTagName('Overview')
		if overview[0].firstChild != None:
			overview=overview[0].firstChild.nodeValue
		else:
			overview=''
		network=serie.getElementsByTagName('Network')
		if network[0].firstChild != None:
			network=network[0].firstChild.nodeValue
		else:
			network=''
		serie_json={
			"id":id,
			"name":name,
			"banner":banner,
			"overview":overview,
			"network": network,
			"favorited_by":[]
		}
		serie_id=collection_serie.insert(serie_json)
		r=requests.get('http://thetvdb.com/api/'+API_KEY+'/series/'+id+'/all/en.xml')
		xml_episodes=unicode(r.text)
		xml_episodes=xml_episodes.encode("utf-8")
		xml_episodes = minidom.parseString(xml_episodes)
		episodes = xml_episodes.getElementsByTagName('Episode')
		for episode in episodes:
			id_episode=episode.getElementsByTagName('id')
			if id_episode[0].firstChild != None:
				id_episode=id_episode[0].firstChild.nodeValue
			else:
				id_episode=''
			combined_season=episode.getElementsByTagName('Combined_season')
			if combined_season[0].firstChild != None:
				combined_season=combined_season[0].firstChild.nodeValue	
			else:
				combined_season=''	
			combined_episodenumber=episode.getElementsByTagName('Combined_episodenumber')
			if combined_episodenumber[0].firstChild != None:
				combined_episodenumber=combined_episodenumber[0].firstChild.nodeValue
			else:
				combined_episodenumber=''
			overview=episode.getElementsByTagName('Overview')
			if overview[0].firstChild != None:
				overview=overview[0].firstChild.nodeValue
			else:
				overview=''
			firstAired=episode.getElementsByTagName('FirstAired')
			if firstAired[0].firstChild != None:
				firstAired=firstAired[0].firstChild.nodeValue
				firstAired=firstAired.split("-")
				firstAired=datetime(int(firstAired[0]),int(firstAired[1]),int(firstAired[2]))
			else:
				firstAired=''
				firstAired=datetime(2050,1,1)
			episode_name=episode.getElementsByTagName('EpisodeName')
			if episode_name[0].firstChild != None:
				episode_name=episode_name[0].firstChild.nodeValue
			else:
				episode_name=''
			rating=episode.getElementsByTagName('Rating')
			if rating[0].firstChild != None:
				rating=rating[0].firstChild.nodeValue
			else:
				rating=''
			filename=episode.getElementsByTagName('filename')
			if filename[0].firstChild != None:
				filename=filename[0].firstChild.nodeValue
				url="http://thetvdb.com/banners/"+filename
				index=filename.rindex('/')
				filename="static/"+filename[index+1:]
				response = requests.get(url, stream=True)
				with open(filename, 'wb') as out_file:
					shutil.copyfileobj(response.raw, out_file)
				del response
			else:
				filename=''	
			episode_json={
				"id":id_episode,
				"combined_season":combined_season,
				"combined_episodenumber":combined_episodenumber,
				"serie_id":serie_id,
				"filename":filename,
				"overview":overview,
				"episode_name":episode_name,
				"firstAired": firstAired,
				"rating":rating
			}
			collection_episode.insert(episode_json)
		break