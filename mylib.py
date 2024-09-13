# -*- coding: UTF-8 -*-
import sqlite3
from sqlite3 import Error
from datetime import datetime, timezone
import re

#EMAIL
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# TODO
available_statuses = ["draft/pending","scheduled-publication","modified-by-editor","published"]


def create_connection(db_file):
  """ create a database connection to the SQLite database
    specified by db_file
  :param db_file: database file
  :return: Connection object or None
  """
  conn = None
  try:
    conn = sqlite3.connect(db_file)
    return conn
  except Error as e:
    print(e)
 
  return conn

def create_table(conn, create_table_sql):
  """ create a table from the create_table_sql statement
  :param conn: Connection object
  :param create_table_sql: a CREATE TABLE statement
  :return:
  """
  try:
    c = conn.cursor()
    c.execute(create_table_sql)
  except Error as e:
    print(e)

def select(conn, query):

  res = []
  conn.row_factory = sqlite3.Row
  c = conn.cursor()
  c.execute(query)
  for r in c.fetchall():
    res.append(dict(r))
  return res

def update(conn, query):
  res = []
  #conn.row_factory = sqlite3.Row
  c = conn.cursor()
  c.execute(query)
  conn.commit()
  numRows = c.rowcount
  return numRows

def insert_harvestingOperation(conn, op):
  """
  Create a new operation into the harvestingOperation table
  :param conn:
  :param op:
  :return: operation id
  """
  sql = ''' INSERT INTO harvestingOperation(date,byAgent,type,dataFile,dataFileWithPath)
        VALUES(?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, op)
  conn.commit()
  return cur.lastrowid

def insert_zenodoItem(conn, item):
  """
  Create a new item into the zenodoItem table
  :param conn:
  :param item:
  :return: item id
  """
  sql = ''' INSERT INTO zenodoItem(date,doiResource,doiUrlResource,idHarvestingOperation)
        VALUES(?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, item)
  conn.commit()
  return cur.lastrowid

def insert_multipleMediaItem(conn, item, itemid=None):
  """
  Create a new item into the multipleMediaItem table
  :param conn:
  :param item:
  :return: item id
  """
  if itemid is not None:
    sql = ''' INSERT INTO multipleMediaItem(id,creationDate,byAgent,type,status,publicationDate,idHarvestingOperation)
          VALUES(?,?,?,?,?,?,?) '''
    item = (itemid,) + item
  else:
    sql = ''' INSERT INTO multipleMediaItem(creationDate,byAgent,type,status,publicationDate,idHarvestingOperation)
          VALUES(?,?,?,?,?,?) '''

  cur = conn.cursor()
  cur.execute(sql, item)
  conn.commit()
  return cur.lastrowid
  
def insert_zenodoMMRelation(conn, relation):
  """
  Create a new relation into the zenodoMMRelation table
  :param conn:
  :param relation:
  :return: relation id
  """
  sql = ''' INSERT INTO zenodoMMRelation(idZenodoItem,idMultipleMedia)
        VALUES(?,?) '''
  cur = conn.cursor()
  cur.execute(sql, relation)
  conn.commit()
  return cur.lastrowid
    
def insert_facebookPost(conn, post, postid=None):
  """
  Create a new post into the facebookPost table
  :param conn:
  :param post:
  :return: post id
  """
  if postid is not None:
    sql = ''' INSERT INTO facebookPost(id,lastModDate, msg, imageUrl, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?,?) '''
    post = (postid,) + post
  else:
    sql = ''' INSERT INTO facebookPost(lastModDate, msg, imageUrl, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, post)
  conn.commit()
  return cur.lastrowid

def insert_linkedinPost(conn, post, postid=None):
  """
  Create a new post into the linkedinPost table
  :param conn:
  :param post:
  :return: post id
  """
  if postid is not None:
    sql = ''' INSERT INTO linkedinPost(id, lastModDate, msg, imageUrl, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?,?) '''
    post = (postid,) + post
  else:
    sql = ''' INSERT INTO linkedinPost(lastModDate, msg, imageUrl, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, post)
  conn.commit()
  return cur.lastrowid
  
def insert_xPost(conn, post, postid=None):
  """
  Create a new post into the xPost table
  :param conn:
  :param post:
  :return: post id
  """
  if postid is not None:
    sql = ''' INSERT INTO xPost(id, lastModDate, msg, imageUrl, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?,?) '''
    post = (postid,) + post
  else:
    sql = ''' INSERT INTO xPost(lastModDate, msg, imageUrl, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, post)
  conn.commit()
  return cur.lastrowid


def insert_feedItem(conn, item, itemid=None):
  """
  Create a new item into the feedItem table
  :param conn:
  :param item:
  :return: item id
  """
  if itemid is not None:
    sql = ''' INSERT INTO feedItem(id,lastModDate, title, link, description, category, enclosure, doiResource, doiUrlResource, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
    item = (itemid,) + item
  else:
    sql = ''' INSERT INTO feedItem(lastModDate, title, link, description, category, enclosure, doiResource, doiUrlResource, modifiedBy, status, scheduledPublicationDate, publicationDate, idMultipleMedia)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, item)
  conn.commit()
  return cur.lastrowid


def get_mediaitem(db_filename, itemid=None):
  if itemid is None:
    return {}
  
  res = {}
  # create a database connection
  conn = create_connection(db_filename)
  if conn is not None:
    # recupero dati nel DB
    queryMMI = f"""SELECT *
          FROM multipleMediaItem
          WHERE 
            id = {itemid}
          ORDER BY id"""
    mmi_res = select(conn, queryMMI)
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
    facebook_res = select(conn, queryFacebook)
    if len(facebook_res) != 1:
      res["data"]["facebook"] = None
    else:
      res["data"]["facebook"] = facebook_res[0]
    
    queryLinkedin = f"""SELECT *
          FROM linkedinPost
          WHERE 
            idMultipleMedia = {itemid}
          ORDER BY id"""
    linkedin_res = select(conn, queryLinkedin)
    if len(linkedin_res) != 1:
      res["data"]["linkedin"] = None
    else:
      res["data"]["linkedin"] = linkedin_res[0]
    
    queryX = f"""SELECT *
          FROM xPost
          WHERE 
            idMultipleMedia = {itemid}
          ORDER BY id"""
    x_res = select(conn, queryX)
    if len(x_res) != 1:
      res["data"]["x"] = None
    else:
      res["data"]["x"] = x_res[0]
    
    queryFeed = f"""SELECT *
          FROM feedItem
          WHERE 
            idMultipleMedia = {itemid}
          ORDER BY id"""
    feed_res = select(conn, queryFeed)
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
  num_rows = update(conn, update_social)
  return num_rows


def updateFeed(conn, mmiCreationDate, data):
  #currDT = datetime.now(timezone.utc).astimezone().isoformat()
  #insert_feedItem(conn, (currDT, title, el["doi_url"], el["description"], el["category"], enclosure, el["doi"], el["doi_url"], "Media Data Center", DEFAULT_MEDIA_STATUS, None, None, multipleMediaItemId))
  
  
  #imageUrl = f"""'{data['imageUrl'].replace("'","''")}'""" if type(data['imageUrl']) == str else "NULL" #facebook['imageUrl']
  # sostituisco la data di ultima modifica con quella attuale
  lastModDate = datetime.now(timezone.utc).astimezone().isoformat()
  modifiedBy = f"""'{data['modifiedBy'].replace("'","''")}'""" if type(data['modifiedBy']) == str else "NULL" #facebook['modifiedBy']
  title = f"""'{data['title'].replace("'", "''")}'""" if type(data['title']) == str else "NULL" 
  description = f"""'{data['description'].replace("'", "''")}'""" if type(data['description']) == str else "NULL" 
  link = f"""'{data['link'].replace("'", "''")}'""" if type(data['link']) == str else "NULL" 
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
  update_social = f"""UPDATE feedItem 
        SET lastModDate = '{lastModDate}',
            modifiedBy = {modifiedBy},
            title = {title},
            description = {description},
            link = {link},
            scheduledPublicationDate = {scheduledPublicationDate},
            status = '{status}'
        WHERE
            idMultipleMedia = {data['id']}"""
  #print(update_facebook)
  num_rows = update(conn, update_social)
  return num_rows


def updateMultipleMediaItem(db_filename, data):
  # Get the JSON data from the request
  #data = request.get_json()
  mm = data['multipleMediaItem']
  facebook = data['data']['facebook']
  linkedin = data['data']['linkedin']
  x = data['data']['x']
  feed = data['data']['feed']
  # Print the data to the console
  print(data)
  
  # create a database connection
  conn = create_connection(db_filename)
   
  # recupero data creazione del MMI
  if conn is not None:
    queryCreationDate = f"""SELECT creationDate
        FROM multipleMediaItem
        WHERE 
          id = {mm['id']}
        ORDER BY id"""
    temp = select(conn, queryCreationDate)
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
    num_rows = updateFeed(conn, mmiCreationDate, feed)
    if type(num_rows) != int:
      return num_rows
    elif num_rows != 1:
      return {"Error": f"Problem(s) updating the feed"}
    
    # Return a success message
    return f"JSON received! - modified {num_rows} rows."
    

def compute_nav(db_filename, itemid):
  nav = {"first": None, "prev": None, "next": None, "last": None}
  if itemid is None:
    return nav
  conn = create_connection(db_filename)
  # recupero id dei multipleMediaItem
  if conn is not None:
    # PREV
    query = f"""SELECT id 
      FROM multipleMediaItem
      WHERE id < {itemid} AND id > 0
      ORDER BY id DESC"""
    prevs = select(conn, query)
    if len(prevs) > 0:
      nav["prev"] = prevs[0]["id"]
    # FIRST
    if len(prevs) > 1:
      nav["first"] = prevs[-1]["id"]
    # NEXT
    query = f"""SELECT id 
      FROM multipleMediaItem
      WHERE id > {itemid} AND id > 0
      ORDER BY id ASC"""
    nexts = select(conn, query)
    if len(nexts) > 0:
      nav["next"] = nexts[0]["id"]
    # LAST
    if len(nexts) > 1:
      nav["last"] = nexts[-1]["id"]
  return nav

class SimpleEmail:

  def __init__(self, SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD):
    self.SMTP_SERVER = SMTP_SERVER
    self.SMTP_PORT = SMTP_PORT 
    self.SENDER_EMAIL = SENDER_EMAIL
    self.SENDER_PASSWORD = SENDER_PASSWORD
   
  def send_mm_notification(self, RECEIVER_EMAILS, subject, MEDDIADATACENTER_EDITOR_URL, multipleMediaItemIds):
    # Create a secure SSL context
    # TODO: QUI O NEL COSTRUTTORE?
    self.context = ssl.create_default_context()
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = self.SENDER_EMAIL
    message["To"] = RECEIVER_EMAILS

    # Create the plain-text and HTML version of your message
    #page_url = f"{MEDDIADATACENTER_EDITOR_URL}{multipleMediaItemId}"
    #page_url = f"{MEDDIADATACENTER_EDITOR_URL}{multipleMediaItemId}"

    page_links_text = "\n".join([f"- {MEDDIADATACENTER_EDITOR_URL}{mmiId}" for mmiId in multipleMediaItemIds])
    page_links_html = "<ol>\n<li>" + \
      "</li>\n<li>".join([f"<a href='{MEDDIADATACENTER_EDITOR_URL}{mmiId}'>{MEDDIADATACENTER_EDITOR_URL}{mmiId}</a>" for mmiId in multipleMediaItemIds]) + \
      "</ol>\n"

    text = f"""Dear FOSSR Media Editor,
New media contents have been created by the Media Data Center agent.
You're invited to check the posts and publish them at the following link(s):
{page_links_text}. 
Best regards,
The FOSSR Media Data Center Agent
"""

    html = f"""
    <html>
      <body>
        <p>Dear FOSSR Media Editor,</p>
        <p>A new media content has been created by the Media Data Center agent.</p>
        <p>You're invited to check the posts and publish them at the following link(s):</p>
        {page_links_html} 
        <p>Best regards,</p>
        <p>The FOSSR Media Data Center Agent</p>
      </body>
    </html> 
    """

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Try to log in to server and send email
    try:
      server = smtplib.SMTP(self.SMTP_SERVER,self.SMTP_PORT)
      #server.ehlo() # Can be omitted
      server.starttls(context=self.context) # Secure the connection
      #server.ehlo() # Can be omitted
      server.login(self.SENDER_EMAIL, self.SENDER_PASSWORD)
      # TODO: Send email here
      server.sendmail(self.SENDER_EMAIL, RECEIVER_EMAILS.split(","), message.as_string())
    except Exception as e:
      # Print any error messages to stdout
      print(e)
    finally:
      server.quit() 

"""
def insert_multipleMediaItem(conn, op):
  '''
  Create a new operation into the multipleMediaItem table
  :param conn:
  :param op:
  :return: operation id
  '''
  sql = ''' INSERT INTO multipleMediaItem(date,byAgent,type,dataFile,dataFileWithPath)
        VALUES(?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, op)
  conn.commit()
  return cur.lastrowid

def insert_facebookPost(conn, post):
  '''
  Create a new post into the facebookPost table
  :param conn:
  :param post:
  :return: post id
  '''
  sql = ''' INSERT INTO facebookPost(date, doiResource, doiUrlResource, msg, image_url, status, idMediaContent, modifiedBy)
        VALUES(?,?,?,?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, post)
  conn.commit()
  return cur.lastrowid

def insert_rssFeed(conn, feed, mediaContents = None):
  '''
  Create a new item into the rssFeed table
  :param conn:
  :param feed:
  :param mediaContents (OPTIONAL): list of media contents objects [{"url": "URL1", "type": "TYPE1", "medium": "MEDIUM1"}, ...]
  :return: feed id
  '''
  sql = ''' INSERT INTO rssFeed(doiResource, doiUrlResource, date, title, link, description, category, enclosures, status, idMediaContent, modifiedBy)
        VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
  cur = conn.cursor()
  cur.execute(sql, feed)
  idFeed = cur.lastrowid
  # add mediaContent objects (es. images) - OPTIONAL
  if mediaContents is not None:
    for mediaContent in mediaContents:
      sql = ''' INSERT INTO rssMediaContent(url, type, medium)
            VALUES(?,?,?) '''
      cur = conn.cursor()
      cur.execute(sql, (mediaContent["url"], mediaContent["type"], mediaContent["medium"]))
      idMediaContent = cur.lastrowid
      
      sql = ''' INSERT INTO hasMediaContent(rssFeedId, rssMediaContentId)
            VALUES(?,?) '''
      cur = conn.cursor()
      cur.execute(sql, (idFeed, idMediaContent))        
  conn.commit()
  return idFeed
"""
