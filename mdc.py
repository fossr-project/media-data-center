from flask import Flask, request, render_template, redirect
#from flask import render_template 
from flask_cors import CORS
import mylib
import json
from datetime import datetime, timezone

import sqlite3

import configparser
config = configparser.ConfigParser()
config.read("conf.ini")

RSS_FILE = config["DEFAULT"]["RSS_FILE"]
ATOM_FILE = config["DEFAULT"]["ATOM_FILE"]
DB_FILENAME = config["DEFAULT"]["DB_FILENAME"]

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

@app.route("/mediadatacenter/mediaitem/", methods=["POST", "GET"])
@app.route("/mediadatacenter/mediaitem/<path:itemid>", methods=["POST", "GET"])
def mdc(itemid=None):
  if request.method == "POST":
    if itemid is None:
      mi = mylib.get_mediaitem(DB_FILENAME, 0)
    else:
      mi = mylib.get_mediaitem(DB_FILENAME, itemid)
    mi["data"]["facebook"]["msg"] = request.form["facebook_msg"]
    mi["data"]["linkedin"]["msg"] = request.form["linkedin_msg"]
    mi["data"]["x"]["msg"] = request.form["x_msg"]
    mi["data"]["feed"]["title"] = request.form["feed_title"]
    mi["data"]["feed"]["description"] = request.form["feed_description"]
    mi["data"]["feed"]["link"] = request.form["feed_link"]
    mi["data"]["facebook"]["modifiedBy"] = mi["data"]["linkedin"]["modifiedBy"] = mi["data"]["x"]["modifiedBy"] = mi["data"]["feed"]["modifiedBy"] = "FOSSR Editor"
    if request.form["mi_scheduled_pubdate"] == "":      
      mi["data"]["facebook"]["scheduledPublicationDate"] = mi["data"]["linkedin"]["scheduledPublicationDate"] = mi["data"]["x"]["scheduledPublicationDate"] = mi["data"]["feed"]["scheduledPublicationDate"] = None
      mi["multipleMediaItem"]["status"] = mi["data"]["facebook"]["status"] = mi["data"]["linkedin"]["status"] = mi["data"]["x"]["status"] = mi["data"]["feed"]["status"] = "modified-by-editor"
    else:
      mi["data"]["facebook"]["scheduledPublicationDate"] = mi["data"]["linkedin"]["scheduledPublicationDate"] = mi["data"]["x"]["scheduledPublicationDate"] = mi["data"]["feed"]["scheduledPublicationDate"] = f"{request.form['mi_scheduled_pubdate']}:00.000000+02:00"
      mi["multipleMediaItem"]["status"] = mi["data"]["facebook"]["status"] = mi["data"]["linkedin"]["status"] = mi["data"]["x"]["status"] = mi["data"]["feed"]["status"] = "scheduled-publication"

    # TODO:
    # - imageUrl
    
    currDate = datetime.now(timezone.utc).astimezone() #datetime.now(timezone.utc).strftime("%d/%m/%Y at %H:%M:%S")
    scheduledPubDate = "" if (mi['data']['facebook']['scheduledPublicationDate'] is None) else mi['data']['facebook']['scheduledPublicationDate'][:16]
    if itemid is None:
      conn = mylib.create_connection(DB_FILENAME)
   
      if conn is not None:
        itemid = mylib.insert_multipleMediaItem(conn, (currDate.isoformat(),"FOSSR Editor","manual",mi["multipleMediaItem"]["status"],None,None))
        mylib.insert_facebookPost(conn, (currDate.isoformat(), request.form["facebook_msg"], None, "FOSSR Editor", mi["data"]["facebook"]["status"], mi["data"]["facebook"]["scheduledPublicationDate"], None, itemid))
        mylib.insert_linkedinPost(conn, (currDate.isoformat(), request.form["linkedin_msg"], None, "FOSSR Editor", mi["data"]["linkedin"]["status"], mi["data"]["linkedin"]["scheduledPublicationDate"], None, itemid))
        mylib.insert_xPost(conn, (currDate.isoformat(), request.form["x_msg"], None, "FOSSR Editor", mi["data"]["x"]["status"], mi["data"]["x"]["scheduledPublicationDate"], None, itemid))
        mylib.insert_feedItem(conn, (currDate.isoformat(), request.form["feed_title"], request.form["feed_link"], request.form["feed_description"], None, None, None, None, "FOSSR Editor", mi["data"]["feed"]["status"], mi["data"]["feed"]["scheduledPublicationDate"], None, itemid))
      nav = mylib.compute_nav(DB_FILENAME, itemid)
      # NOTE:
      # 1. CODE = 307 => mantengo metodo della richiesta originale (ossia POST)
      # 2. LA REDIRECT FA UNA UPDATE NEL DATABASE DEL UN RECORD CHE HA APPENA INSERITO - PERO' IN QUESTO MODO METTO IN HTML IL MESSAGGIO DELL'ULTIMO SALVATAGGIO
      #      => TODO: SISTEMARE???
      return redirect(f"/mediadatacenter/mediaitem/{itemid}", code=307) 
    else:
      mylib.updateMultipleMediaItem(DB_FILENAME, mi)
      nav = mylib.compute_nav(DB_FILENAME, itemid)
      return render_template('MediaDataCenter.html', mediaitem=mi, action=f"/mediadatacenter/mediaitem/{itemid}", savedatetime=currDate.strftime("%d/%m/%Y at %H:%M:%S"), scheduled_pub_date=scheduledPubDate, navigation=nav)
  else:
    nav = mylib.compute_nav(DB_FILENAME, itemid)
    if itemid is None:
      mi = mylib.get_mediaitem(DB_FILENAME, 0)
      return render_template('MediaDataCenter.html', mediaitem=mi, action=f"/mediadatacenter/mediaitem/", savedatetime=None, scheduled_pub_date="", navigation=nav)
    else:
      mi = mylib.get_mediaitem(DB_FILENAME, itemid)
      scheduledPubDate = "" if (mi['data']['facebook']['scheduledPublicationDate'] is None) else mi['data']['facebook']['scheduledPublicationDate'][:16]
      return render_template('MediaDataCenter.html', mediaitem=mi, action=f"/mediadatacenter/mediaitem/{itemid}", savedatetime=None, scheduled_pub_date=scheduledPubDate, navigation=nav)

'''
@app.route("/mediadatacenter/mediaitem/<path:itemid>", methods=["POST"])
def mdc_g(itemid=None):
  mi_scheduled_pubdate = request.form["mi_scheduled_pubdate"]
  facebook_msg = request.form["facebook_msg"]
  linkedin_msg = request.form["linkedin_msg"]
  x_msg = request.form["x_msg"]
  feed_title  = request.form["feed_title"]
  feed_description = request.form["feed_description"]
  feed_link = request.form["feed_link"]
  print(feed_description)
  return "Pizza"

@app.route("/mediadatacenter/mediaitem/<path:itemid>", methods=["GET"])
def mdc_p(itemid=None):
  mi = get_mediaitem(itemid)
  #print(mi)
  return render_template('MediaDataCenter.html', mediaitem=mi, action=f"/mediadatacenter/mediaitem/{itemid}")


@app.route("/mediadatacenter/mediaitem_old/<path:itemid>")
def get_mediaitem(itemid=None):
  res = {}
  
  print(itemid)
  # create a database connection
  conn = mylib.create_connection(DB_FILENAME)
   
  if conn is not None:
    # recupero dati nel DB
    queryMMI = f"""SELECT *
          FROM multipleMediaItem
          WHERE 
            id = {itemid}
          ORDER BY id"""
    mmi_res = mylib.select(conn, queryMMI)
    if len(mmi_res) != 1:
      return {"error": f"multiple media item not found (id = {itemid})"}
    mmi = mmi_res
    res["multipleMediaItem"] = mmi[0]
    
    res["data"] = {}
    
    queryFacebook = f"""SELECT *
          FROM facebookPost
          WHERE 
            idMultipleMedia = {itemid}
          ORDER BY id"""
    facebook_res = mylib.select(conn, queryFacebook)
    if len(facebook_res) != 1:
      res["data"]["facebook"] = None
    else:
      res["data"]["facebook"] = facebook_res[0]
    
    queryLinkedin = f"""SELECT *
          FROM linkedinPost
          WHERE 
            idMultipleMedia = {itemid}
          ORDER BY id"""
    linkedin_res = mylib.select(conn, queryLinkedin)
    if len(linkedin_res) != 1:
      res["data"]["linkedin"] = None
    else:
      res["data"]["linkedin"] = linkedin_res[0]
    
    queryX = f"""SELECT *
          FROM xPost
          WHERE 
            idMultipleMedia = {itemid}
          ORDER BY id"""
    x_res = mylib.select(conn, queryX)
    if len(x_res) != 1:
      res["data"]["x"] = None
    else:
      res["data"]["x"] = x_res[0]
    
    queryFeed = f"""SELECT *
          FROM feedItem
          WHERE 
            idMultipleMedia = {itemid}
          ORDER BY id"""
    feed_res = mylib.select(conn, queryFeed)
    if len(feed_res) != 1:
      res["data"]["feed"] = None
    else:
      res["data"]["feed"] = feed_res[0]
      
    conn.close()
  else:
    print("Error! cannot create the database connection.")
  
  return res

  
def isValidDate(d):
  timezone_pattern = "^(0[0-9]|1[0-2]):00"
  # controllo che separatore con parte timezone sia + o -
  if d[26] not in "+-":
    return False
  if len(d) == 32:
    isodate = d[:26]
    timezone = d[27:]
  try:
    datetime.fromisoformat(isodate)
  except ValueError:
    return False
  if not re.match(timezone_pattern, timezone):
    return False
  return True

def updateSocialMedia(conn, socialName, mmiCreationDate, data):
  imageUrl = f"""'{data['imageUrl'].replace("'","''")}'""" if type(data['imageUrl']) == str else "NULL" #facebook['imageUrl']
  # sostituisco la data di ultima modifica con quella attuale
  lastModDate = datetime.now(timezone.utc).astimezone().isoformat()
  modifiedBy = f"""'{data['modifiedBy'].replace("'","''")}'""" if type(data['modifiedBy']) == str else "NULL" #facebook['modifiedBy']
  msg = f"""'{data['msg'].replace("'", "''")}'""" if type(data['msg']) == str else "NULL" #facebook['msg']
  # controllo che formato data sia corretto e che successiva (>) a creation date del multipleMediaItem
  if data['scheduledPublicationDate'] is not None:
    if isValidDate(data['scheduledPublicationDate']) and (data['scheduledPublicationDate'] > mmiCreationDate):
      scheduledPublicationDate = f"""'{data['scheduledPublicationDate']}'"""
    else:
      return {f"Error": f"The {socialName} publication date is not valid ({data['scheduledPublicationDate']} - MMI creationDate={mmiCreationDate})"}
  else:
    scheduledPublicationDate = "NULL"
  if data['status'] in available_statuses:
    status = data['status']
  else:
    status = "scheduled-publication"
  update_social = f"""UPDATE {socialName}Post 
        SET imageUrl = {imageUrl},
            lastModDate = '{lastModDate}',
            modifiedBy = {modifiedBy},
            msg = {msg},
            scheduledPublicationDate = {scheduledPublicationDate},
            status = '{status}'
        WHERE
            idMultipleMedia = {data['id']}"""
  #print(update_facebook)
  num_rows = mylib.update(conn, update_social)
  return num_rows

@app.route("/json", methods=["PUT"])
def myjson():
  # Get the JSON data from the request
  data = request.get_json()
  mm = data['multipleMediaItem']
  facebook = data['data']['facebook']
  linkedin = data['data']['linkedin']
  x = data['data']['x']
  feed = data['data']['feed']
  # Print the data to the console
  print(data)
  
  # create a database connection
  conn = mylib.create_connection(DB_FILENAME)
   
  # recupero data creazione del MMI
  if conn is not None:
    queryCreationDate = f"""SELECT creationDate
        FROM multipleMediaItem
        WHERE 
          id = {mm['id']}
        ORDER BY id"""
    temp = mylib.select(conn, queryCreationDate)
    if (len(temp) == 1) and isValidDate(temp[0]["creationDate"]):
      mmiCreationDate = temp[0]["creationDate"]
    else:
      return {"Error": f"The creation date in the DB is not valid (MMI id={mm['id']})"}
    #print("mmiCreationDate:", mmiCreationDate)
    
    ################
    ### FACEBOOK ###
    ################
    num_rows = updateSocialMedia(conn, "facebook", mmiCreationDate, facebook)
    if type(num_rows) != int:
      return num_rows
    elif num_rows != 1:
      return {"Error": f"Problem(s) updating the facebook post"}
      
    ################
    ### LINKEDIN ###
    ################
    num_rows = updateSocialMedia(conn, "linkedin", mmiCreationDate, linkedin)
    if type(num_rows) != int:
      return num_rows
    elif num_rows != 1:
      return {"Error": f"Problem(s) updating the linkedin post"}
      
    ################
    ###    X     ###
    ################
    num_rows = updateSocialMedia(conn, "x", mmiCreationDate, x)
    if type(num_rows) != int:
      return num_rows
    elif num_rows != 1:
      return {"Error": f"Problem(s) updating the X post"}

    ################
    ###   FEED   ###
    ################

    # Return a success message
    return f"JSON received! - modified {num_rows} rows."
'''

"""
# RSS
@app.route("/rss") 
def serve_rss(): 
  message = "FOSSR RSS"
  return "{{url_for('static', filename='rss.xml')}}"#render_template(RSS_FILE, message=message)

# ATOM
@app.route("/atom") 
def serve_atom(): 
  message = "FOSSR ATOM"
  return render_template(ATOM_FILE, message=message)
"""
