import os
import tempfile
import distutils.dir_util

from django.conf import settings
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.utils import simplejson as json
from django.http import QueryDict
import views
import flickr
import statichosting

# These take a long time, so they're disabled by default.
RUN_FLICKR_API_VERIFICATION_TESTS = False

ROOT = os.path.abspath(os.path.dirname(__file__))
path = lambda *x: os.path.join(ROOT, *x)

SAMPLE_IMG = path('sample_data', 'test_image.png')
SAMPLE_INDEX = path('sample_data', 'index.html')
SAMPLE_CSS = path('sample_data', 'sample.css')
SAMPLE_JS = path('sample_data', 'sample.js')

def test_apply_reasonable_defaults_works():
    '''
    >>> obj = QueryDict('foo=%20&a=%20')
    >>> new = views.apply_reasonable_defaults(obj, foo='hi', bar='there')
    >>> new['foo']
    'hi'
    >>> new['bar']
    'there'
    >>> 'a' in new
    False
    '''
    
    pass

def test_clean_upload_params_works():
    '''
    >>> views.clean_upload_params(QueryDict(''))['title']
    'Untitled'
    >>> stuff = QueryDict('source_url=http://foo.com/')
    >>> views.clean_upload_params(stuff)['source_title']
    u'http://foo.com/'
    '''
    
    pass

class LocalFileStaticHostingTests(TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        
    def tearDown(self):
        distutils.dir_util.remove_tree(self.dir)

    def test_local_file_backend(self):
        tempdir = self.dir
        backend = statichosting.LocalFileBackend(root=tempdir,
                                                 url='http://foo.com/')
        storage = statichosting.Storage(backend)
        factory = RequestFactory()
        req = factory.post('', dict(
            index_file=open(SAMPLE_INDEX, 'rb'),
            index_support_files='3',
            index_support_file_0=open(SAMPLE_IMG, 'rb'),
            index_support_file_0_dir='files',
            index_support_file_1=open(SAMPLE_CSS, 'rb'),
            index_support_file_1_dir='files/css',
            index_support_file_2=open(SAMPLE_JS, 'rb'),            
            index_support_file_2_dir='files'            
            ))
        photo_id = '53235'
        url = storage.process(photo_id, req)

        self.assertEqual(url, 'http://foo.com/%s/' % photo_id)

        root = os.path.join(tempdir, photo_id)
        indexpath = os.path.join(root, 'index.html')
        supportpath = os.path.join(root, 'files', 'test_image.png')
        jspath = os.path.join(root, 'files', 'sample.js')        
        csspath = os.path.join(root, 'files', 'css', 'sample.css')
        self.assertEqual(open(indexpath, 'rb').read(),
                         open(SAMPLE_INDEX, 'rb').read())
        self.assertEqual(open(supportpath, 'rb').read(),
                         open(SAMPLE_IMG, 'rb').read())
        self.assertEqual(open(jspath, 'rb').read(),
                         open(SAMPLE_JS, 'rb').read())
        self.assertEqual(open(csspath, 'rb').read(),
                         open(SAMPLE_CSS, 'rb').read())

class FlickrTests(TestCase):
    if RUN_FLICKR_API_VERIFICATION_TESTS:
        def test_flickr_token_is_valid(self):
            api = flickr.get_api()
            api.auth_checkToken()

        def test_flickr_upload_and_delete_work(self):
            photo_id = flickr.upload(filename=SAMPLE_IMG)
            flickr.delete(photo_id)

    def test_shorturl_works(self):
        self.assertEqual(flickr.shorturl('5688591650'),
                         'http://flic.kr/p/9EFw7o')

class ApiTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
    def tearDown(self):
        pass

    def test_upload_returns_method_not_allowed_on_get(self):
        c = Client()
        response = c.get('/upload/')
        self.assertEqual(response.status_code, 405)

    def test_upload_returns_forbidden_with_no_auth_token(self):
        req = self.factory.post('', dict())
        response = views.upload(req)
        self.assertEqual(response.status_code, 403)

    def test_upload_returns_forbidden_with_bad_auth_token(self):
        req = self.factory.post('', dict(auth_token='no u'))
        response = views.upload(req)
        self.assertEqual(response.status_code, 403)

    def test_upload_without_screenshot_returns_400(self):
        req = self.factory.post('', dict(
            auth_token=settings.UPLOAD_AUTH_TOKEN,
            ))
        response = views.upload(req)
        self.assertEqual(response.status_code, 400)

    def test_upload_returns_json_with_expected_args(self):
        req = self.factory.post('', dict(
            auth_token=settings.UPLOAD_AUTH_TOKEN,
            screenshot=open(SAMPLE_IMG, 'rb')
            ))
        
        def fake_upload_to_flickr(some_request):
            self.assertTrue(some_request is req)
            return '5688591650'
        
        response = views.upload(req,
                                upload_to_flickr=fake_upload_to_flickr)
        
        self.assertEqual(response['content-type'], 'application/json')
        obj = json.loads(response.content)
        self.assertEqual(obj['photo_id'], '5688591650')
        self.assertEqual(obj['short_url'], 'http://flic.kr/p/9EFw7o')

    def test_upload_to_flickr_works(self):
        req = self.factory.post('', dict(screenshot=open(SAMPLE_IMG, 'rb')))

        info = {}

        def fake_upload(filename, **kwargs):
            self.assertTrue('filename' not in info)
            info['filename'] = filename
            self.assertTrue(os.path.isfile(filename))
            self.assertEqual(open(SAMPLE_IMG, 'rb').read(),
                             open(filename, 'rb').read())
            return 'fake photo id'

        photo_id = views.upload_to_flickr(req, upload=fake_upload)

        self.assertEqual(photo_id, 'fake photo id') 
        self.assertFalse(os.path.exists(info['filename']))
