from google_photo_sync import *
from client_data import *
from nose.tools import *

email = 'abc@gmail.com'  # Edit and enter your email account
gd_client = OAuth2Login(client_secret, credential_store, email)
current_dir = os.getcwd()
updirectory = current_dir + '\%s\%s' % ('testing_gpsync', 'test_album')
dwlddirectory = updirectory + '\%s' % ('test_album')


def for_album_download(gd_client):  # Function for album download test
    testalbum = find_album(gd_client, 'test_album')
    download_album(gd_client, testalbum, dwlddirectory)
    localphototitle = os.listdir(dwlddirectory)
    return localphototitle  # Returns list of files in downloaded album/directory


def for_album_upload(gd_client):  # Function for album download test
    localAlbums = get_local_albums(find_media(updirectory))
    upload_album(gd_client, 'test_album', localAlbums['test_album'])
    testalbum = find_album(gd_client, 'test_album')
    webphototitle = []
    photos = get_photos_for_picasa_album(gd_client, testalbum)
    for photo in photos:
        webphototitle.append(photo.title.text)
    return webphototitle  # Returns list of files in uploaded album


# Syncing by add test by downloading missing photo in local album
def sync_by_add_1(gd_client):
    photo1path = dwlddirectory + '\%s' % ('testphoto1.jpg')
    os.remove(photo1path)
    localAlbums = get_local_albums(find_media(dwlddirectory))
    webAlbums = get_web_albums(gd_client)
    download_missing_photo(gd_client, ['test_album'], webAlbums, localAlbums)
    localphototitle = os.listdir(dwlddirectory)
    return localphototitle


def sync_by_add_2(gd_client):  # Syncing by addtest by uploading missing photo in Picasa album
    localAlbums = get_local_albums(find_media(dwlddirectory))
    webAlbums = get_web_albums(gd_client)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    for photo in photos:
        if photo.title.text == 'testphoto2.jpg':
            gd_client.Delete(photo)
    upload_missing_photo(gd_client, ['test_album'], localAlbums, webAlbums)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    webphototitle = []
    for photo in photos:
        webphototitle.append(photo.title.text)
    return webphototitle


# Syncing by deletion test by propogating delete at local album to Picasa album
def sync_by_del_1(gd_client):
    photo1path = dwlddirectory + '\%s' % ('testphoto1.jpg')
    os.remove(photo1path)
    localAlbums = get_local_albums(find_media(dwlddirectory))
    webAlbums = get_web_albums(gd_client)
    del_extra_from_web(gd_client, ['test_album'], localAlbums, webAlbums)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    webphototitle = []
    for photo in photos:
        webphototitle.append(photo.title.text)
    return webphototitle


# Syncing by deletion test by propogating delete at Picasa album to local album
def sync_by_del_2(gd_client):
    webAlbums = get_web_albums(gd_client)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    for photo in photos:
        if photo.title.text == 'testphoto2.jpg':
            gd_client.Delete(photo)
    localAlbums = get_local_albums(find_media(dwlddirectory))
    del_extra_from_local(gd_client, ['test_album'], localAlbums, webAlbums)
    localphototitle = os.listdir(dwlddirectory)
    return localphototitle


def setup_module():
    None


def teardown_module():
    testalbum = find_album(gd_client, 'test_album')
    gd_client.Delete(testalbum)
    os.rmdir(dwlddirectory)


def test_album_upload():
    assert_equal(for_album_upload(gd_client), [
                 'testphoto1.jpg', 'testphoto2.jpg'])


def test_album_download():
    print(__name__, ': TestClass.test_method_2()')
    assert_equal(for_album_download(gd_client), [
                 'testphoto1.jpg', 'testphoto2.jpg'])


def test_sync_by_add_1():
    assert_equal(sync_by_add_1(gd_client), [
                 'testphoto1.jpg', 'testphoto2.jpg'])


def test_sync_by_add_2():
    assert_equal(sync_by_add_2(gd_client), [
                 'testphoto1.jpg', 'testphoto2.jpg'])


def test_sync_by_del_1():
    assert_equal(sync_by_del_1(gd_client), ['testphoto2.jpg'])


def test_sync_by_del_2():
    assert_equal(sync_by_del_2(gd_client), [])
