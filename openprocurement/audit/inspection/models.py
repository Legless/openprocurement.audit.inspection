from uuid import uuid4

from openprocurement.api.constants import SANDBOX_MODE
from openprocurement.api.utils import get_now
from openprocurement.api.models import Model, Revision, Period, Identifier, Address, ContactPoint
from openprocurement.api.models import Document
from openprocurement.api.models import schematics_embedded_role, schematics_default_role, IsoDateTimeType, ListType
from schematics.types import StringType, MD5Type, BaseType, BooleanType
from schematics.types.serializable import serializable
from schematics.types.compound import ModelType, DictType
from schematics.transforms import whitelist, blacklist
from schematics.exceptions import ValidationError
from couchdb_schematics.document import SchematicsDocument
from pyramid.security import Allow


class BaseModel(SchematicsDocument, Model):

    @serializable(serialized_name='id')
    def doc_id(self):
        """
        A property that is serialized by schematics exports.
        """
        return self._id

    def import_data(self, raw_data, **kw):
        """
        Converts and imports the raw data into the instance of the model
        according to the fields in the model.
        :param raw_data:
            The data to be imported.
        """
        data = self.convert(raw_data, **kw)
        del_keys = [
            k for k in data.keys()
            if data[k] == self.__class__.fields[k].default
               or data[k] == getattr(self, k)
        ]
        for k in del_keys:
            del data[k]

        self._data.update(data)
        return self


class Inspection(BaseModel):
    class Options:
        roles = {
            'plain': blacklist('_attachments', 'revisions') + schematics_embedded_role,
            'revision': whitelist('revisions'),
            'create': blacklist(
                'revisions', 'dateModified', 'dateCreated',
                'doc_id', '_attachments', 'inspection_id'
            ) + schematics_embedded_role,
            'edit': whitelist("description", "monitoring_ids"),
            'view': blacklist(
                '_attachments', 'revisions',
            ) + schematics_embedded_role,
            'listing': whitelist('dateModified', 'doc_id'),
            'default': schematics_default_role,
        }

    monitoring_ids = ListType(MD5Type, required=True, min_size=1)
    description = StringType(required=True)

    documents = ListType(ModelType(Document), default=list())
    inspection_id = StringType()
    dateModified = IsoDateTimeType()
    dateCreated = IsoDateTimeType(default=get_now)

    revisions = ListType(ModelType(Revision), default=list())
    _attachments = DictType(DictType(BaseType), default=dict())

    def __repr__(self):
        return '<%s:%r-%r@%r>' % (type(self).__name__, self.inspection_id, self.id, self.rev)
