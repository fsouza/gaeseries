from django.db import models

class ListField(models.Field):
    def __init__(self, field_type, *args, **kwargs):
        self.field_type = field_type
        kwargs.setdefault('default', lambda: None if self.null else [])
        if not callable(kwargs['default']):
            default = kwargs['default']
            kwargs['default'] = lambda: default[:]
        super(ListField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        self.field_type.model = cls
        self.field_type.name = name
        super(ListField, self).contribute_to_class(cls, name)

    def db_type(self, connection):
        return 'ListField:' + self.field_type.db_type(connection=connection)

    def call_for_each(self, function_name, values, *args, **kwargs):
        if isinstance(values, (list, tuple)) and len(values):
            for i, value in enumerate(values):
                values[i] = getattr(self.field_type, function_name)(value, *args,
                    **kwargs)
        return values

    def to_python(self, value):
        return self.call_for_each('to_python', value)

    def get_prep_value(self, value):
        return self.call_for_each('get_prep_value', value)

    def get_db_prep_value(self, value, connection, prepared=False):
        return self.call_for_each('get_db_prep_value', value, connection=connection,
            prepared=prepared)

    def get_db_prep_save(self, value, connection):
        return self.call_for_each('get_db_prep_save', value, connection=connection)

    def formfield(self, **kwargs):
        return None

class BlobField(models.Field):
    """
    A field for storing blobs of binary data
    """
    def get_internal_type(self):
        return 'BlobField'

    def formfield(self, **kwargs):
        # A file widget is provided, but use  model FileField or ImageField
        # for storing specific files most of the time
        from .widgets import BlobWidget
        from django.forms import FileField
        defaults = {'form_class': FileField, 'widget': BlobWidget}
        defaults.update(kwargs)
        return super(BlobField, self).formfield(**defaults)

    def get_db_prep_value(self, value, connection, prepared=False):
        try:
            # Sees if the object passed in is file-like
            return value.read()
        except:
            return str(value)

    def get_db_prep_lookup(self, lookup_type, value, connection, prepared=False):
        raise TypeError("BlobFields do not support lookups")

    def value_to_string(self, obj):
        return str(self._get_val_from_obj(obj))
