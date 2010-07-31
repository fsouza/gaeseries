import os

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage
from django.core.files.uploadedfile import UploadedFile
from django.core.files.uploadhandler import FileUploadHandler, \
    StopFutureHandlers
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.utils.encoding import smart_str, force_unicode

from google.appengine.ext.blobstore import BlobInfo, BlobKey, delete, \
    create_upload_url, BLOB_KEY_HEADER, BLOB_RANGE_HEADER

def prepare_upload(request, url, **kwargs):
    return create_upload_url(url), {}

def serve_file(request, file, save_as, content_type, **kwargs):
    if hasattr(file, 'file') and hasattr(file.file, 'blobstore_info'):
        blobkey = file.file.blobstore_info.key()
    elif hasattr(file, 'blobstore_info'):
        blobkey = file.blobstore_info.key()
    else:
        raise ValueError("The provided file can't be served via the "
                         "Google App Engine Blobstore.")
    response = HttpResponse(content_type=content_type)
    response[BLOB_KEY_HEADER] = str(blobkey)
    response['Accept-Ranges'] = 'bytes'
    http_range = request.META.get('HTTP_RANGE')
    if http_range is not None:
        response[BLOB_RANGE_HEADER] = http_range
    if save_as:
        response['Content-Disposition'] = smart_str(u'attachment; filename=%s' % save_as)
    if file.size is not None:
        response['Content-Length'] = file.size
    return response

class BlobstoreStorage(Storage):
    """Google App Engine Blobstore storage backend"""

    def _open(self, name, mode='rb'):
        return BlobstoreFile(name, mode, self)

    def _save(self, name, content):
        name = name.replace('\\', '/')
        if hasattr(content, 'file') and hasattr(content.file, 'blobstore_info'):
            data = content.file.blobstore_info
        elif hasattr(content, 'blobstore_info'):
            data = content.blobstore_info
        else:
            raise ValueError("The App Engine storage backend only supports "
                             "BlobstoreFile instances or File instances "
                             "whose file attribute is a BlobstoreFile.")

        if isinstance(data, (BlobInfo, BlobKey)):
            # We change the file name to the BlobKey's str() value
            if isinstance(data, BlobInfo):
                data = data.key()
            return '%s/%s' % (data, name.lstrip('/'))
        else:
            raise ValueError("The App Engine Blobstore only supports "
                             "BlobInfo values. Data can't be uploaded "
                             "directly. You have to use the file upload "
                             "handler.")

    def delete(self, name):
        delete(self._get_key(name))

    def exists(self, name):
        return self._get_blobinfo(name) is not None

    def size(self, name):
        return self._get_blobinfo(name).size

    def url(self, name):
        raise NotImplementedError()

    def get_valid_name(self, name):
        return force_unicode(name).strip().replace('\\', '/')

    def get_available_name(self, name):
        return name.replace('\\', '/')

    def _get_key(self, name):
        return BlobKey(name.split('/', 1)[0])

    def _get_blobinfo(self, name):
        return BlobInfo.get(self._get_key(name))

class BlobstoreFile(File):
    def __init__(self, name, mode, storage):
        self.name = name
        self._storage = storage
        self._mode = mode
        self.blobstore_info = storage._get_blobinfo(name)

    @property
    def size(self):
        return self.blobstore_info.size

    def read(self, *args, **kwargs):
        raise NotImplementedError()

    def write(self, content):
        raise NotImplementedError()

    def close(self):
        pass

class BlobstoreFileUploadHandler(FileUploadHandler):
    """
    File upload handler for the Google App Engine Blobstore
    """

    def new_file(self, *args, **kwargs):
        super(BlobstoreFileUploadHandler, self).new_file(*args, **kwargs)
        blobkey = self.content_type_extra.get('blob-key')
        self.active = blobkey is not None
        if self.active:
            self.blobkey = BlobKey(blobkey)
            raise StopFutureHandlers()

    def receive_data_chunk(self, raw_data, start):
        """
        Add the data to the StringIO file.
        """
        if not self.active:
            return raw_data

    def file_complete(self, file_size):
        """
        Return a file object if we're activated.
        """
        if not self.active:
            return

        return BlobstoreUploadedFile(
            blobinfo=BlobInfo(self.blobkey),
            charset=self.charset)

class BlobstoreUploadedFile(UploadedFile):
    """
    A file uploaded into memory (i.e. stream-to-memory).
    """
    def __init__(self, blobinfo, charset):
        super(BlobstoreUploadedFile, self).__init__(
            blobinfo, blobinfo.filename, blobinfo.content_type, blobinfo.size,
            charset)
        self.blobstore_info = blobinfo

    def open(self, mode=None):
        pass

    def close(self):
        pass

    def chunks(self, chunk_size=None):
        self.file.seek(0)
        yield self.read()

    def multiple_chunks(self, chunk_size=None):
        # Since it's in memory, we'll never have multiple chunks.
        return False
