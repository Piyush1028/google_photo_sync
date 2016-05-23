import os
import sys
import argparse
import atom
import atom.service
import filecmp
import gdata
import gdata.photos.service
import gdata.media
import gdata.geo
import gdata.gauth
import getpass
import httplib2
import os
import subprocess
import tempfile
import time
import webbrowser
import urllib

from datetime import datetime, timedelta
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from gdata.photos.service import GPHOTOS_INVALID_ARGUMENT, GPHOTOS_INVALID_CONTENT_TYPE, GooglePhotosException

knownExtensions = {
    '.png': 'image/png',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif'}


def OAuth2Login(client_secrets, credential_store, email):
    scope = 'https://picasaweb.google.com/data/'
    user_agent = 'piyush_gpsync'

    storage = Storage(credential_store)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        flow = flow_from_clientsecrets(
            client_secrets, scope=scope, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        uri = flow.step1_get_authorize_url()
        webbrowser.open(uri)
        code = raw_input('Enter the authentication code: ').strip()
        credentials = flow.step2_exchange(code)

    if (credentials.token_expiry - datetime.utcnow()) < timedelta(minutes=5):
        http = httplib2.Http()
        http = credentials.authorize(http)
        credentials.refresh(http)

    storage.put(credentials)

    gd_client = gdata.photos.service.PhotosService(source=user_agent,
                                                   email=email,
                                                   additional_headers={'Authorization': 'Bearer %s' % credentials.access_token})

    return gd_client

# list of photos within a album


def getPhotosForPicasaAlbum(gd_client, album):
    photos = gd_client.GetFeed(
        '/data/feed/api/user/%s/albumid/%s?kind=photo' % (
            gd_client.email, album.gphoto_id.text))
    return photos.entry


def downloadPhoto(url_source, directory, phototitle):
    location = directory + "\%s" % (phototitle)
    print 'downloading %s' % (location)
    urllib.urlretrieve(url_source, location)


def findAlbum(gd_client, title):
    albums = gd_client.GetUserFeed()
    for album in albums.entry:
        if album.title.text == title:
            return album
    return None


def createAlbum(gd_client, title):
    print("Creating album " + title)
    # public, private, protected. private == "anyone with link"
    album = gd_client.InsertAlbum(title=title, summary='', access='protected')
    return album


def findOrCreateAlbum(gd_client, title):
    delay = 1
    while True:
        try:
            album = findAlbum(gd_client, title)
            if not album:
                album = createAlbum(gd_client, title)
            return album
        except gdata.photos.service.GooglePhotosException as e:
            print("caught exception " + str(e))
            print("sleeping for " + str(delay) + " seconds")
            time.sleep(delay)
            delay = delay * 2


def getWebAlbums(gd_client):
    albums = gd_client.GetUserFeed()
    d = {}
    print('WEBALBUMS:')
    for album in albums.entry:
        title = album.title.text
        if title in d:
            print("Duplicate web album:" + title)
        else:
            d[title] = album
        print('title: %s, number of photos: %s' % (album.title.text,
                                                   album.numphotos.text))
    return d


def getPhotosForPicasaAlbum(gd_client, album):  # list of photos within a album
    photos = gd_client.GetFeed(
        '/data/feed/api/user/%s/albumid/%s?kind=photo' % (
            gd_client.email, album.gphoto_id.text))
    return photos.entry


def getContentType(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in knownExtensions:
        return knownExtensions[ext]
    else:
        return None


def isAllowedFile(filename):
    return getContentType(filename)


def findMedia(source):  # path of photos within dir and subdirectories
    arg = {}

    os.path.walk(source, visit, arg)
    # Calls the function visit with arguments (arg, dirname, names)
    # for each directory in the directory tree rooted at path (including path itself).
    # The argument dirname specifies the visited directory,
    #  the argument names lists the files in the directory
    return arg


def visit(arg, dirname, names):
    basedirname = os.path.basename(dirname)
    if basedirname.startswith('.'):
        return
    mediaFiles = [name for name in names if not name.startswith('.') and isAllowedFile(name) and
                  os.path.isfile(os.path.join(dirname, name))]
    count = len(mediaFiles)
    # considering empty albums also
    if count >= 0:
        arg[dirname] = {'files': sorted(mediaFiles)}


# for getting albums in directory and subdirectories along with allowed
# media content
def getLocalAlbums(photos):
    d = {}
    print('LOCALALBUMS:')
    for i in photos:
        base = os.path.basename(i)
        if base in d:
            print("duplicate " + base + ":\n" + i + ":\n" + d[base]['path'])
            raise Exception("duplicate base")
        p = photos[i]
        p['path'] = i
        d[base] = p
        print('title: %s, number of photos: %s' %
              (base, len(d[base]['files'])))
    return d


def compareLocalToWeb(local, web):
    localOnly = []
    both = []
    webOnly = []
    for i in local:
        if i in web:
            both.append(i)
        else:
            localOnly.append(i)
    for i in web:
        if i not in local:
            webOnly.append(i)
    print 'Albums present only on Google Photos:\n', webOnly
    print 'Albums present only on local directory:\n', localOnly
    return {'localOnly': localOnly, 'both': both, 'webOnly': webOnly}


# Download

# to download albums present only on the web
def dowloadWebOnlyAlbums(gd_client, webonlyalbums, webAlbums):
    for album in webonlyalbums:
        album_id = webAlbums[album].gphoto_id.text
        location = destination + '\%s' % (webAlbums[album].title.text)
        if not os.path.exists(location):
            os.makedirs(location)
        photos = getPhotosForPicasaAlbum(gd_client, webAlbums[album])
        for photo in photos:
            # added now 23.05
            if (isAllowedFile(photo.title.text)):
                downloadPhoto(photo.content.src, location, photo.title.text)

# Upload

# for local only albums, to upload on web


def uploadLocalOnlyAlbums(gd_client, localonlyalbums, localAlbums):
    for album in localonlyalbums:
        uploadAlbum(gd_client, album, localAlbums[album])

# to upload photos of albums present only on local directory


def uploadAlbum(gd_client, dir, localAlbum):
    webAlbum = findOrCreateAlbum(gd_client, dir)
    for pic in localAlbum['files']:
        localPath = os.path.join(localAlbum['path'], pic)
        upload(gd_client, localPath, webAlbum, pic)


def upload(gd_client, localPath, album, fileName):
    print("Uploading " + localPath)
    contentType = getContentType(fileName)
    picasa_photo = gdata.photos.PhotoEntry()
    picasa_photo.title = atom.Title(text=fileName)
    picasa_photo.summary = atom.Summary(text='', summary_type='text')
    delay = 1
    while True:
        try:
            gd_client.InsertPhoto(album, picasa_photo,
                                  localPath, content_type=contentType)
            break
        except gdata.photos.service.GooglePhotosException as e:
            print("Got exception " + str(e))
            print("retrying in " + str(delay) + " seconds")
            time.sleep(delay)
            delay = delay * 2

# Sync

# IN CASE WANT TO DOWLOAD EXTRA FILE FROM CLOUD OR UPLOAD EXTRA FILE IN
# DIR TO CLOUD

# dwld missing file in local album


def downloadMissingPhoto(gd_client, commonalbum, webAlbums, localAlbums):
    for album in commonalbum:
        album_id = webAlbums[album].gphoto_id.text
        location = localAlbums[album]['path']
        webPhotos = getPhotosForPicasaAlbum(gd_client, webAlbums[album])
        for photo in webPhotos:
            if (photo.title.text not in localAlbums[album]['files'] and isAllowedFile(photo.title.text)):
                downloadPhoto(photo.content.src, location, photo.title.text)

# upload missing file in picasa album


def uploadMissingPhoto(gd_client, commonalbum, localAlbums, webAlbums):
    for album in commonalbum:
        webPhotos = getPhotosForPicasaAlbum(gd_client, webAlbums[album])
        webPhotoList = []
        for pics in webPhotos:
            webPhotoList.append(pics.title.text)
        for photo in localAlbums[album]['files']:
            if photo not in webPhotoList:
                path = localAlbums[album]['path'] + '\%s' % (photo)
                upload(gd_client, path, webAlbums[album], photo)


# In case  you want to propagate delete to/from cloud/directory

# delete extra photo from cloud album
def delFromWeb(gd_client, dir, localAlbums, webAlbums):
    for album in dir:
        webPhotos = getPhotosForPicasaAlbum(gd_client, webAlbums[album])
        for photo in webPhotos:
            if photo.title.text not in localAlbums[album]['files']:
                print 'Deleting %s from Album: %s' % (photo.title.text, webAlbums[album].title.text)
                gd_client.Delete(photo)

# delete extra from local directory


def delFromLocal(gd_client, dir, localAlbums, webAlbums):
    for album in dir:
        webPhotos = getPhotosForPicasaAlbum(gd_client, webAlbums[album])
        webPhotoList = []
        for pics in webPhotos:
            webPhotoList.append(pics.title.text)
        for photo in localAlbums[album]['files']:
            if photo not in webPhotoList:
                path = localAlbums[album]['path'] + '\%s' % (photo)
                print 'deleting %s' % path
                os.remove(path)


if __name__ == '__main__':
    email = raw_input('enter the email for google photo account --> ')
    destination = raw_input(
        'enter the local directory where you have the albums --> ')

    # options for oauth2 login
    configdir = os.path.expanduser('C:\Users\Piyush Kumar\Desktop\gdata-python-client-master')
    client_secrets = os.path.join(configdir, 'client_secrets.json')
    credential_store = os.path.join(configdir, 'credentials.dat')

    gd_client = OAuth2Login(client_secrets, credential_store, email)

    x = 1
    while(x == 1):
        time.sleep(5)
        # getting list of albums in picasa
        webAlbums = getWebAlbums(gd_client)

        # getting list of albums in directory
        localAlbums = getLocalAlbums(findMedia(destination))

        # gets a dict in return with keys localonly, both, webonly and contents as
        # list respective album names
        albumDiff = compareLocalToWeb(localAlbums, webAlbums)

        print 'Enter D, U, S or E \n D to download albums on web not present locally,\
         \n U to upload albums from dir not present on web,\
         \n S to Sync the albums present at both places,\n E to exit'
        todo = raw_input()
        if (todo == 'D'):
            if (len(albumDiff['webOnly']) == 0):
                print'All albums already present locally\n'
            else:
                dowloadWebOnlyAlbums(gd_client, albumDiff[
                                     'webOnly'], webAlbums)

        elif (todo == 'U'):
            if (len(albumDiff['localOnly']) == 0):
                print'All albums already present in picasa\n'
            else:
                uploadLocalOnlyAlbums(gd_client, albumDiff[
                                      'localOnly'], localAlbums)

        elif (todo == 'S'):
            htsync = raw_input(
                'Enter A or R \n A for adding missing\n R for deleting extra\n')
            if (htsync == 'A'):
                downloadMissingPhoto(gd_client, albumDiff[
                                     'both'], webAlbums, localAlbums)
                uploadMissingPhoto(gd_client, albumDiff[
                                   'both'], localAlbums, webAlbums)
                print 'Syncing complete by adding missing files\n'

            elif (htsync == 'R'):
                delFromWeb(gd_client, albumDiff[
                           'both'], localAlbums, webAlbums)
                delFromLocal(gd_client, albumDiff[
                             'both'], localAlbums, webAlbums)
                print 'Syncing complete by deleting extra files\n'

            else:
                print 'wrong command'
                continue
        elif (todo == 'E'):
            x = 0
        else:
            print 'wrong command'
