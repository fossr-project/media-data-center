import requests
import json
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
from num2words import num2words
from mylib import *
import os
import sys
import configparser

config = configparser.ConfigParser()
config.read("conf.ini")

DB_FILENAME = config["DEFAULT"]["DB_FILENAME"]
ONE_POST_MANY_ZENODO_RECORDS = config.getboolean("ZENODO","ONE_POST_MANY_ZENODO_RECORDS")
#https://www.rssboard.org/rss-specification#ltenclosuregtSubelementOfLtitemgt
#https://feedgen.kiesow.be/api.entry.html#feedgen.entry.FeedEntry.enclosure
ACCESS_TOKEN = config["ZENODO"]["ACCESS_TOKEN"]
FOSSR_COMMUNITY_ID = config["ZENODO"]["FOSSR_COMMUNITY_ID"]
ZENODO_FILE = config["ZENODO"]["ZENODO_FILE"]
RSS_FILE = config["ZENODO"]["RSS_FILE"]
ATOM_FILE = config["ZENODO"]["ATOM_FILE"]
# the default status of the post/feed generated by this component
DEFAULT_MEDIA_STATUS = config["ZENODO"]["DEFAULT_MEDIA_STATUS"]

#################
# EMAIL EDITORS #
#################
SMTP_SERVER = config["EMAIL"]["SMTP_SERVER"]
SMTP_PORT = config["EMAIL"]["SMTP_PORT"]
SENDER_EMAIL = config["EMAIL"]["SENDER_EMAIL"]
SENDER_PASSWORD = config["EMAIL"]["SENDER_PASSWORD"]
RECEIVER_EMAILS = config["EMAIL"]["EDITORS_EMAILS"]
#MEDDIADATACENTER_EDITOR_URL = config["DEFAULT"]["MEDDIADATACENTER_EDITOR_URL"]
MEDDIADATACENTER_EDITOR_HOST = config["DEFAULT"]["MEDDIADATACENTER_EDITOR_HOST"]
MEDDIADATACENTER_EDITOR_PATH = config["DEFAULT"]["MEDDIADATACENTER_EDITOR_PATH"]
MEDDIADATACENTER_EDITOR_URL = MEDDIADATACENTER_EDITOR_HOST + MEDDIADATACENTER_EDITOR_PATH

EMAIL_SUBJECT = config["EMAIL"]["EMAIL_SUBJECT"]

"""
r = requests.get("https://zenodo.org/api/deposit/depositions", params={"access_token": ACCESS_TOKEN})
print(r.status_code)
data = r.json()
print(json.dumps(data, indent=2))

with open("test1", "w") as fpoggi_file:
  json.dump(data, fpoggi_file, indent=2, sort_keys=True)
"""


# Nota: non sono riuscito ad usare parametro custom per filtrare sulla data di pubblicazione, modifca o update 
r = requests.get("https://zenodo.org/api/records", params={"communities": FOSSR_COMMUNITY_ID}) #"q": "*", "access_token": ACCESS_TOKEN})
#print(r.status_code)
data = r.json()
#print(json.dumps(data, indent=2))
if not os.path.exists("data/"): 
  os.makedirs("data/") 
 
my_zenodo_file = ZENODO_FILE.replace(".json", f"_{datetime.now().isoformat()}.json")

with open(my_zenodo_file, "w") as community_file:
  json.dump(data, community_file, indent=2, sort_keys=True)

"""
###############################
# CREATE RSS AND ATOM FILES ###
###############################
fg = FeedGenerator()

fg.title("FOSSR Project @Zenodo - Fostering Open Science in Social Science Research")
fg.subtitle("The channel with updates about FOSSR resources published on Zenodo")
fg.link( href="https://zenodo.org/communities/fossr/records", rel="self" )
#print(datum["doi"],datum["doi_url"])
fg.id("http://fossr.eu/channels")
fg.author( {"name":"Mr Blue","email":"TODO@example.de"} )
#fg.link( href=datum["doi_url"], rel="alternate" )
#fg.logo("http://ex.com/logo.jpg")
fg.language("en")

for datum in data["hits"]["hits"]:
  #created, updated, modified
  # "ciaoo" > "ciao" (inizio uguali più altri caratteri è maggiore nell"ordinamento)
  if datum["created"] >= "2023-12-15":
    #temp = {datum["modified"]: "modified", datum["updated"]: "updated", datum["created"]: "created"}
    #temp_sorted = sorted(temp)
    #print(temp_sorted, type(temp_sorted))
    if (datum["updated"] > datum["created"]) or (datum["modified"] > datum["created"]):
      if datum["updated"] > datum["modified"]:
        pubDate = datum["updated"]
        title = f"The resource {datum['metadata']['title']} has been updated."
      else:
        pubDate = datum["modified"]
        title = f"The resource {datum['metadata']['title']} has been modified."
    else:
      pubDate = datum["created"]
      title = f"A new resource entitled {datum['metadata']['title']} has been published."
    
    fe = fg.add_entry()
    fe.guid(datum["doi_url"], True) #datum["doi"]
    #fe.id(datum["doi"])
    fe.title(title)
    fe.description(datum["metadata"]["description"])
    #print("MD:", datum["metadata"])
    #print("RT:", datum["metadata"]["resource_type"])
    #print("Title:", datum["metadata"]["resource_type"]["title"])
    fe.category({"term": datum["metadata"]["resource_type"]["title"], "scheme": "https://schema.datacite.org/"}) #oppure datum["metadata"]["resource_type"]["type"]
    for f in datum["files"]:
      # ATOM feeds can furthermore contain several enclosures while RSS may contain only one. That is why this method, if repeatedly called, will add more than one enclosures to the feed. However, only the last one is used for RSS.
      fe.enclosure(url=f["links"]["self"], type="application/pdf")
    fe.source("http://fossr.eu/RSS")
    fe.pubDate(pubDate)
    fe.link(href=datum["doi_url"])
  #print(type(datum))
  #print(datum)
  #for key in datum.keys():
  #  print(key)#, "\n") #["conceptdoi"],datum["doi_url"])
  #break

if not os.path.exists("static/"): 
  os.makedirs("static/") 
fg.rss_file(RSS_FILE, pretty=True, encoding="UTF-8")
fg.atom_file(ATOM_FILE, pretty=True, encoding="UTF-8")
"""

# SETUP EMAIL
mymail = SimpleEmail(SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD)

# create a database connection
conn = create_connection(DB_FILENAME)
 
# insert data into DB
if conn is not None:
  currDT = datetime.now(timezone.utc).astimezone().isoformat()
  # insert row into harvestingOperation table
  harvestingOperationId = insert_harvestingOperation(conn, (currDT, "Media Data Center", "zenodo", my_zenodo_file.split("/")[-1], my_zenodo_file))
  
  # recupero doi delle risorse zenodo nel DB
  queryDoiZenodo = '''SELECT doiResource
        FROM zenodoItem
        WHERE
          doiResource IS NOT NULL
        ORDER BY doiResource'''
  doisZenodo = [doiDict["doiResource"] for doiDict in select(conn, queryDoiZenodo)]
  
  # inserisco righe (una per ogni nuovo doi zenodo) nella tabella zenodoItem, multipleMediaItem e zenodoMMRelation
  temp_list = []
  for datum in data["hits"]["hits"]:
    
    doi = datum["doi"]
    if doi in doisZenodo:
      #print("SKIP")
      continue 
    if datum["created"] >= "2023-12-15":
      print("SKIP CREATION DATE")
      continue
    temp = {}
    temp["doi"] = doi
    temp["doi_url"] = datum["doi_url"]
    temp["title"] = datum['metadata']['title']
    temp["description"] = datum["metadata"]["description"]
    temp["category"] = datum["metadata"]["resource_type"]["title"]
    temp_list.append(temp)

  if len(temp_list) > 0:
    multipleMediaItemId_list = []
    if ONE_POST_MANY_ZENODO_RECORDS:
      multipleMediaItemId = insert_multipleMediaItem(conn, (currDT, "Media Data Center", "zenodo", DEFAULT_MEDIA_STATUS, None, harvestingOperationId))
      multipleMediaItemId_list.append(multipleMediaItemId)
      for el in temp_list:
        zenodoItemId = insert_zenodoItem(conn, (currDT, el["doi"], el["doi_url"], harvestingOperationId))
        insert_zenodoMMRelation(conn, (zenodoItemId, multipleMediaItemId))
        #################
        # FEED
        title = f"A new resource entitled '{el['title']}' has been published on zenodo."
        # TODO: per atom dovrebbe essere una lista...
        enclosure = None
        insert_feedItem(conn, (currDT, title, el["doi_url"], el["description"], el["category"], enclosure, el["doi"], el["doi_url"], "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
        #################

      msg = f"{num2words(len(temp_list)).capitalize()} new resources have been published on zenodo:\n"
      msg += "\n".join(f"- Title: '{el['title']}' - see {el['doi_url']}." for el in temp_list)
      facebookPostId = insert_facebookPost(conn, (currDT, msg, None, "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
      linkedinPostId = insert_linkedinPost(conn, (currDT, msg, None, "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
      xPostId = insert_xPost(conn, (currDT, msg, None, "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
      
    else:
      for el in temp_list:
        multipleMediaItemId = insert_multipleMediaItem(conn, (currDT, "Media Data Center", "zenodo", DEFAULT_MEDIA_STATUS, None, harvestingOperationId))
        multipleMediaItemId_list.append(multipleMediaItemId)
        zenodoItemId = insert_zenodoItem(conn, (currDT, el["doi"], el["doi_url"], harvestingOperationId))
        insert_zenodoMMRelation(conn, (zenodoItemId, multipleMediaItemId))
        msg = f"A new resource entitled '{el['title']}' has been published - see {el['doi_url']}."
        facebookPostId = insert_facebookPost(conn, (currDT, msg, None, "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
        linkedinPostId = insert_linkedinPost(conn, (currDT, msg, None, "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
        xPostId = insert_xPost(conn, (currDT, msg, None, "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
        
        #################
        # FEED
        title = f"A new resource entitled '{el['title']}' has been published on zenodo."
        # TODO: per atom dovrebbe essere una lista...
        enclosure = None
        insert_feedItem(conn, (currDT, title, el["doi_url"], el["description"], el["category"], enclosure, el["doi"], el["doi_url"], "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
        #################
          
    mymail.send_mm_notification(RECEIVER_EMAILS, EMAIL_SUBJECT, MEDDIADATACENTER_EDITOR_URL, multipleMediaItemId_list)

  conn.close()
else:
  print("Error! cannot create the database connection.")



#https://zenodo.org/api/communities/bb9fca56-6a00-447c-b37e-09edf2952918/records?q=&sort=newest&page=1&size=10
#https://zenodo.org/api/communities/bb9fca56-6a00-447c-b37e-09edf2952918/records?q=&sort=newest&page=2&size=10

'''
sys.exit()
      
  for datum in data["hits"]["hits"]:
    doi = datum["doi"]
    if doi in doisZenodo:
      #print("SKIP")
      continue 
    if datum["created"] >= "2023-12-15":
      print("SKIP CREATION DATE")
      #continue
    doi_url = datum["doi_url"]
    title = datum['metadata']['title']
    description = datum["metadata"]["description"]
    msg = f"A new resource entitled '{title}' has been published - see {doi_url}."
    
    zenodoItemId = mylib.insert_zenodoItem(conn, (currDT, doi, doi_url, harvestingOperationId))
    
    if ONE_POST_MANY_ZENODO_RECORDS:
      # creo un solo MMItem per il primo record zenodo
      if multipleMediaItemId is None:
        multipleMediaItemId = mylib.insert_multipleMediaItem(conn, (currDT, "Media Data Center", "zenodo", DEFAULT_MEDIA_STATUS, None, harvestingOperationId))
        # TODO FACEBOOK
    else:
      # creo molti MMItem, uno per ogni record zenodo 
      multipleMediaItemId = mylib.insert_multipleMediaItem(conn, (currDT, "Media Data Center", "zenodo", DEFAULT_MEDIA_STATUS, None, harvestingOperationId))
      facebookPostId = mylib.insert_facebookPost(conn, (currDT, msg, None, "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
    mylib.insert_zenodoMMRelation(conn, (zenodoItemId, multipleMediaItemId))
    
    
    #facebookId = mylib.insert_facebookPost(conn, (currDT, doi, doi_url, f"msg: {title}", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Columba_livia_%28Madrid%2C_Spain%29_006.jpg/220px-Columba_livia_%28Madrid%2C_Spain%29_006.jpg", DEFAULT_MEDIA_STATUS, multipleMediaItemId, None))
    
  sys.exit()
  
  
  
  multipleMediaItemId = mylib.insert_multipleMediaItem(conn, (currDT, "Media Data Center", "zenodo", my_zenodo_file.split("/")[-1], my_zenodo_file))
  
  # recupero doi risorse collegate ai post nel DB
  queryDoiFacebook = """SELECT *
        FROM facebookPost
        WHERE 
          doiResource IS NOT NULL 
        ORDER BY doiResource"""
  cur = conn.cursor()
  rows = cur.execute(queryDoiFacebook)
  doisFacebook = [row[2] for row in rows]
    
  # inserisco righe (una per ogni doi zenodo per cui non esiste già un post) nella tabella facebookPost 
  for datum in data["hits"]["hits"]:
    doi = datum["doi"]
    if doi in doisFacebook:
      #print("SKIP")
      continue 
    if datum["created"] >= "2023-12-15":
      print("SKIP CREATED")
      #continue
    doi_url = datum["doi_url"]
    title = datum['metadata']['title']
    description = datum["metadata"]["description"]
    msg = f"A new resource entitled 'title' has been published - see {doi_url}."
    facebookId = mylib.insert_facebookPost(conn, (currDT, doi, doi_url, f"msg: {title}", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Columba_livia_%28Madrid%2C_Spain%29_006.jpg/220px-Columba_livia_%28Madrid%2C_Spain%29_006.jpg", DEFAULT_MEDIA_STATUS, multipleMediaItemId, None))
    #print("INSERITO")
  
  # recupero doi risorse collegate agli rss feed nel DB
  queryDoiRss = """SELECT *
        FROM rssFeed
        WHERE 
          doiResource IS NOT NULL 
        ORDER BY doiResource"""
  cur = conn.cursor()
  rows = cur.execute(queryDoiRss)
  doisRss = [row[1] for row in rows]
  #print("DOIRSS:", doisRss)
  
  # inserisco righe (una per ogni doi zenodo per cui non esiste già un rss feed) nella tabella rssFeed 
  for datum in data["hits"]["hits"]:
    doi = datum["doi"]
    #print("DOI DATUM:", doi)
    if doi in doisRss:
      continue 
    if datum["created"] >= "2023-12-15":
      print("SKIP CREATED")
      continue
    doi_url = datum["doi_url"]
    title = f"A new resource entitled {datum['metadata']['title']} has been published - see {doi_url}."
    link = href=datum["doi_url"]
    #description = fe.description(datum["metadata"]["description"])
    description = datum["metadata"]["description"]
    category = datum["metadata"]["resource_type"]["title"]
    # ATOM feeds can furthermore contain several enclosures while RSS may contain only one. That is why this method, if repeatedly called, will add more than one enclosures to the feed. However, only the last one is used for RSS.
    enclosures = [f["links"]["self"] for f in datum["files"]]
    enclosures_str = ",".join(enclosures)
    rssId = mylib.insert_rssFeed(conn, (doi, doi_url, currDT, title, link, description, category, enclosures_str, DEFAULT_MEDIA_STATUS, multipleMediaItemId, None))
    #testImgs = [{"url": "URL1", "type": "TYPE1", "medium": "MEDIUM1"}, {"url": "URL2", "type": "TYPE2", "medium": "MEDIUM2"}, {"url": "URL3", "type": "TYPE3", "medium": "MEDIUM3"}]
    #rssId = mylib.insert_rssFeed(conn, (doi, doi_url, currDT, title, link, description, category, enclosures_str, DEFAULT_MEDIA_STATUS, multipleMediaItemId, None), testImgs)
    
  conn.close()
else:
  print("Error! cannot create the database connection.")
'''
