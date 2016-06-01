#! /usr/bin/python2

#This is a Google Photos Two Way Sync Utility enabling syncing between Local Albums and Google Photos/Picasa Albums.

import os
import sys
import atom
import atom.service
import gdata
import gdata.photos.service
import gdata.media
import gdata.geo
import gdata.gauth
import httplib2
import time
import webbrowser
import urllib

from datetime import datetime, timedelta
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from gdata.photos.service import GPHOTOS_INVALID_ARGUMENT, GPHOTOS_INVALID_CONTENT_TYPE, GooglePhotosException


# This application now supports only image files of
# types:'.png','.jpg','.jpeg' and '.gif'
known_extensions = {
    '.png': 'image/png',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif'}


def OAuth2Login(client_secrets, credential_store, email):
    scope = 'https://picasaweb.google.com/data/'
    user_agent = 'piyush_gpsync'  # name of application

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

def get_content_type(filename):  # Checking extension to get the type of file
    ext = os.path.splitext(filename)[1].lower()
    if ext in known_extensions:
        return known_extensions[ext]
    else:
        return None


def is_allowed_file(filename):
    return get_content_type(filename)


def get_web_albums(gd_client):  # Getting a dictionary of picasa albums
    albums = gd_client.GetUserFeed()
    d = {}
    print('WEBALBUMS:')
    for album in albums.entry:
        title = album.title.text
        # Checking duplicate albums as duplicate is possible in Picasa but not
        # in local
        if title in d:
            print("Duplicate web album:" + title)
        else:
            d[title] = album
        print('title: %s, number of photos: %s' % (album.title.text,
                                                   album.numphotos.text))
    return d


# returns dictionary with keys as local album name
# of the form {'directory':{'files':['image1','imagr2']}..}
def visit(arg, dirname, names):
    mediaFiles = []
    for name in names:
        if is_allowed_file(name) and os.path.isfile(os.path.join(dirname, name)):
            mediaFiles.append(name)
    count = len(mediaFiles)
    # not considering empty albums also
    if count > 0:
        arg[dirname] = {'files': sorted(mediaFiles)}


def find_media(source):  # path of photos within dir and subdirectories
    arg = {}
    os.path.walk(source, visit, arg)
    # Calls the function visit with arguments (arg, dirname, names)
    # for each directory in the directory tree rooted at source (including source itself).
    # The argument dirname specifies the visited directory,
    #  the argument names lists the files in the directory
    return arg


# for getting albums in directory and subdirectories along with allowed
# media content
# returns dictionary of album of the form
# {'AlbumName1':{'files':['image1','imagr2']'path': 'path of AlbumName1'}...}
def get_local_albums(photos):
    localalbums = {}
    print('LOCALALBUMS:')
    for i in photos:
        album = os.path.basename(i)  # obtaining album name from directory
        if album in localalbums:
            print("duplicate " + album + ":\n" + i +
                  ":\n" + localalbums[album]['path'])
            raise Exception("duplicate album")
        p = photos[i]
        p['path'] = i
        localalbums[album] = p
        print('title: %s, number of photos: %s' %
              (album, len(localalbums[album]['files'])))
    return localalbums


# to compare albums present at local directory and picasa account
def compare_local_to_web(local, web):
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


# to get photos in particular picasa album of original size along with all
# Metadata
def get_photos_for_picasa_album(gd_client, album):
    photos = gd_client.GetFeed(
        '/data/feed/api/user/%s/albumid/%s?kind=photo&imgmax=d' % (
            gd_client.email, album.gphoto_id.text))  # modifications done to get Photos along with Metadata
    return photos.entry


# To find album on picasa account
def find_album(gd_client, title):
    albums = gd_client.GetUserFeed()
    for album in albums.entry:
        if album.title.text == title:
            return album
    return None


# To create album on picasa account
def create_album(gd_client, title):
    print("Creating album " + title)
    # access types:public, private, protected. private == "anyone with link"
    album = gd_client.InsertAlbum(title=title, summary='', access='protected')
    return album


def find_or_create_album(gd_client, title):
    delay = 1
    while True:
        try:
            album = find_album(gd_client, title)
            if not album:
                album = create_album(gd_client, title)
            return album
        except gdata.photos.service.GooglePhotosException as e:
            print("caught exception " + str(e))
            print("sleeping for " + str(delay) + " seconds")
            time.sleep(delay)
            if delay <= 8:
                delay = delay * 2
            else:
                print 'Failed, check solution and try later'
                break


# Download photo to a local album
def download_photo(url_source, directory, phototitle):
    delay = 1
    location = directory + "\%s" % (phototitle)
    print 'Downloading: %s in Local Album: %s \n' % (phototitle, os.path.basename(directory))
    while True:
        try:
            urllib.urlretrieve(url_source, location)
            break
        except:
            print("retrying in " + str(delay) + " seconds")
            time.sleep(delay)
            if delay <= 8:
                delay = delay * 2
            else:
                print 'Download failed'
                break


def download_album(gd_client, webAlbum, location):
    if not os.path.exists(location):
        os.makedirs(location)
    photos = get_photos_for_picasa_album(gd_client, webAlbum)
    for photo in photos:
        if (is_allowed_file(photo.title.text)):
            download_photo(photo.content.src, location, photo.title.text)
    print 'Completed download of Album: %s \n' % (webAlbum.title.text)


# To download albums present only on the web
def download_webonly_albums(gd_client, webonlyalbums, webAlbums):
    for album in webonlyalbums:
        webalbum = webAlbums[album]
        album_id = webalbum.gphoto_id.text
        location = destination + '\%s' % (webalbum.title.text)
        download_album(gd_client, webalbum, location)


# Upload

def upload_photo(gd_client, localPath, album, fileName):
    print 'Uploading: %s in Picasa Album: %s' % (os.path.basename(localPath), album.title.text)
    contentType = get_content_type(fileName)
    picasa_photo = gdata.photos.PhotoEntry()
    picasa_photo.title = atom.Title(text=fileName)
    picasa_photo.summary = atom.Summary(text='', summary_type='text')
    delay = 1
    while True:
        try:
            gd_client.InsertPhoto(album, picasa_photo,
                                  localPath, content_type=contentType)
            break
        except gdata.photos.service.GooglePhotosException as e:  # retry on upload failure
            print("Got exception " + str(e))
            print("retrying in " + str(delay) + " seconds")
            time.sleep(delay)
            if delay <= 8:
                delay = delay * 2
            else:
                print 'Upload failed, check solution and try later'
                break


# To upload a local album in Picasa account
def upload_album(gd_client, albumname, localAlbum):
    webAlbum = find_or_create_album(gd_client, albumname)
    for pic in localAlbum['files']:
        localPath = os.path.join(localAlbum['path'], pic)
        upload_photo(gd_client, localPath, webAlbum, pic)
    print 'Completed upload of Album: %s' % (albumname)


# For uploading Albums present only locally to Picasa album
def upload_localonly_albums(gd_client, localonlyalbums, localAlbums):
    for album in localonlyalbums:
        upload_album(gd_client, album, localAlbums[album])


# Sync

# Sync by adding any different file in local album to picasa album or vice
# versa

# Download missing file in local album
def download_missing_photo(gd_client, commonalbum, webAlbums, localAlbums):
    for album in commonalbum:
        album_id = webAlbums[album].gphoto_id.text
        location = localAlbums[album]['path']
        webPhotos = get_photos_for_picasa_album(gd_client, webAlbums[album])
        for photo in webPhotos:
            if (photo.title.text not in localAlbums[album]['files'] and is_allowed_file(photo.title.text)):
                download_photo(photo.content.src, location, photo.title.text)


# Upload missing file in picasa album
def upload_missing_photo(gd_client, commonalbum, localAlbums, webAlbums):
    for album in commonalbum:
        webPhotos = get_photos_for_picasa_album(gd_client, webAlbums[album])
        webPhotoList = []
        for pics in webPhotos:
            webPhotoList.append(pics.title.text)
        for photo in localAlbums[album]['files']:
            if photo not in webPhotoList:
                path = localAlbums[album]['path'] + '\%s' % (photo)
                upload_photo(gd_client, path, webAlbums[album], photo)


# Sync by deleting any extra file in Picasa album with respect to Local
# album and vice versa

# Delete extra photo from picasa album
def del_extra_from_web(gd_client, both, localAlbums, webAlbums):
    for album in both:
        webPhotos = get_photos_for_picasa_album(gd_client, webAlbums[album])
        for photo in webPhotos:
            if photo.title.text not in localAlbums[album]['files']:
                print 'Deleting: %s from Picasa Album: %s' % (photo.title.text, webAlbums[album].title.text)
                gd_client.Delete(photo)


# Delete extra from local album
def del_extra_from_local(gd_client, both, localAlbums, webAlbums):
    for album in both:
        webPhotos = get_photos_for_picasa_album(gd_client, webAlbums[album])
        webPhotoList = []
        for pics in webPhotos:
            webPhotoList.append(pics.title.text)
        for photo in localAlbums[album]['files']:
            if photo not in webPhotoList:
                path = localAlbums[album]['path'] + '\%s' % (photo)
                print 'Deleting: %s from Local Album: %s' % (photo, album)
                os.remove(path)


if __name__ == '__main__':
    email = raw_input('Enter the email for google photo account --> ')
    destination = raw_input(
        'Enter the base directory where you have the local albums --> ')
    assert (os.path.exists(destination)), 'No such directory exists'

    from client_data import *

    gd_client = OAuth2Login(client_secret, credential_store, email)

    while True:
        # adding delay as sometimes change done at picasa album takes time to
        # get reflected
        time.sleep(3)
        # getting list of albums in picasa account
        webAlbums = get_web_albums(gd_client)

        # getting list of albums in directory
        localAlbums = get_local_albums(find_media(destination))

        # gets a dict in return with keys localonly, both, webonly and contents as
        # list of respective album names
        albumDiff = compare_local_to_web(localAlbums, webAlbums)

        print 'Enter D, U, S or E \n D to download albums on web not present locally,\
         \n U to upload albums from directory not present on web,\
         \n S to Sync the albums present at both places,\n E to exit'
        todo = raw_input()
        if (todo == 'D' or todo == 'd'):
            if (len(albumDiff['webOnly']) == 0):
                print'All albums already present locally\n'
            else:
                download_webonly_albums(gd_client, albumDiff[
                    'webOnly'], webAlbums)
                print 'ALL MISSING ALBUMS DOWLOADED SUSSEFULLY\n'

        elif (todo == 'U'or todo == 'u'):
            if (len(albumDiff['localOnly']) == 0):
                print'All albums already present in picasa\n'
            else:
                upload_localonly_albums(gd_client, albumDiff[
                    'localOnly'], localAlbums)
                print 'ALL MISSING ALBUMS UPLOADED SUSSEFULLY\n'

        elif (todo == 'S' or todo == 's'):
            htsync = raw_input(
                'Enter A or R depending on how you want to sync \n A for adding missing photos \
            \n R for deleting any extra photo\n')
            if (htsync == 'A' or htsync == 'a'):
                download_missing_photo(gd_client, albumDiff[
                    'both'], webAlbums, localAlbums)
                upload_missing_photo(gd_client, albumDiff[
                    'both'], localAlbums, webAlbums)
                print 'SYNCING COMPLETED BY ADDING MISSING PHOTOS\n'

            elif (htsync == 'R' or htsync == 'r'):
                del_extra_from_web(gd_client, albumDiff[
                    'both'], localAlbums, webAlbums)
                del_extra_from_local(gd_client, albumDiff[
                    'both'], localAlbums, webAlbums)
                print 'SYNCING COMPLETED BY DELETING EXTRA PHOTOS\n'

            else:
                print 'wrong command'
                continue
        elif (todo == 'E' or todo == 'e'):
            os.remove(credential_store)
            break
        else:
            print 'wrong command'
