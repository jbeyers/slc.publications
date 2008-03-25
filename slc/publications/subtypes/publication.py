from zope.interface import implements
from Products.CMFPlone import PloneMessageFactory as _
from Products.Archetypes import atapi 
from Products.validation import V_REQUIRED
from archetypes.schemaextender.interfaces import ISchemaExtender, IOrderableSchemaExtender
from archetypes.schemaextender.field import ExtensionField
from slc.publications.config import AUTHOR

class ExtensionFieldMixin:
    def translationMutator(self, instance):
        return self.getMutator(instance)

class CoverImageField(ExtensionField, ExtensionFieldMixin, atapi.ImageField):
    """ The cover image """

class AuthorField(ExtensionField, ExtensionFieldMixin, atapi.StringField):
    """ The Publicaion Author"""

class ISBNField(ExtensionField, ExtensionFieldMixin, atapi.StringField):
    """ The Publications ISBN """

class OrderIdField(ExtensionField, ExtensionFieldMixin, atapi.StringField):
    """ The Publications Order ID """

class ForSaleField(ExtensionField, ExtensionFieldMixin, atapi.BooleanField):
    """ The Publication id for sale? """

class ChaptersField(ExtensionField, ExtensionFieldMixin, atapi.LinesField):
    """ The Publication Chapters """

class MetadataUploadField(ExtensionField, ExtensionFieldMixin, atapi.FileField):
    """ The Publication Metadata as ini upload """

class OwnerPasswordField(ExtensionField, ExtensionFieldMixin, atapi.StringField):
    """ The Publication PDFs owner password """

class UserPasswordField(ExtensionField, ExtensionFieldMixin, atapi.StringField):
    """ The Publication PDFs user password """


class SchemaExtender(object):
    implements(IOrderableSchemaExtender)

    _fields = [
            CoverImageField('cover_image',
                schemata='publication',
                sizes={'cover':(70,100)},
                languageIndependent=True,
                widget=atapi.ImageWidget(
                    label = _(u'label_cover_image', default=u'Cover Image'),
                    description=_(u'description_cover_image', default=u'Upload a cover image. Leave empty to have the system autogenerate one for you.'),
                ),
                translation_mutator="translationMutator",
            ),
            AuthorField('author',
                schemata='publication',
                languageIndependent=True,
                default=AUTHOR,
                widget=atapi.StringWidget(
                    label = _(u'label_author', default=u'Author'),
                    description=_(u'description_author', default=u'Fill in the Name of the Author of this Publication.'),
                ),
                translation_mutator="translationMutator",
            ),
            ISBNField('isbn',
                schemata='publication',
                languageIndependent=False,
                widget=atapi.StringWidget(
                    label = _(u'label_isbn', default=u'ISBN'),
                    description=_(u'description_isbn', default=u'Fill in the ISBN Number of this Publication.'),
                ),
                translation_mutator="translationMutator",
            ),
            OrderIdField('order_id',
                schemata='publication',
                languageIndependent=False,
                widget=atapi.StringWidget(
                    label = _(u'label_order_id', default=u'Order ID'),
                    description=_(u'description_order_id', default=u'Fill in the Order ID of this Publication.'),
                ),
                translation_mutator="translationMutator",
            ),
            ForSaleField('for_sale',
                schemata='publication',
                languageIndependent=True,
                widget=atapi.BooleanWidget(
                    label = _(u'label_for_sale', default=u'For sale?'),
                    description=_(u'description_for_sale', default=u'Is this Publication for sale?'),
                ),
                translation_mutator="translationMutator",
            ),
            ChaptersField('chapters',
                schemata='publication',
                languageIndependent=True,
                widget=atapi.LinesWidget(
                    label = _(u'label_chapters', default=u'Chapters'),
                    description=_(u'description_chapters', default=u'Chapters of this Publication. Specify the Link targets defined in your pdf file, one per line.'),
                ),
                translation_mutator="translationMutator",
            ),
            MetadataUploadField('metadata_upload',
                schemata='publication',
                languageIndependent=True,
                widget=atapi.FileWidget(
                    label = _(u'label_metadata_upload', default=u'Metadata INI upload'),
                    description=_(u'description_metadata_upload', default=u'Upload Metadata in INI style format.'),
                ),
                translation_mutator="translationMutator",
            ),
            OwnerPasswordField('owner_password',
                schemata='publication',
                languageIndependent=False,
                widget=atapi.StringWidget(
                    label = _(u'label_owner_password', default=u'Owner Password'),
                    description=_(u'description_owner_password', default=u'If this publication is protected, speciy the pdf owner password if you want to parse the file.'),
                ),
                translation_mutator="translationMutator",
            ),
            UserPasswordField('user_password',
                schemata='publication',
                languageIndependent=False,
                widget=atapi.StringWidget(
                    label = _(u'label_user_password', default=u'User Password'),
                    description=_(u'description_user_password', default=u'If this publication is protected, speciy the pdf user password if you want to parse the file.'),
                ),
                translation_mutator="translationMutator",
            ),
            ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self._fields

    def getOrder(self, original):
        publication = original.get('publication', [])

        #publication.remove('')

        publication.insert(0, 'author')
        publication.insert(1, 'isbn')
        publication.insert(2, 'order_id')
        publication.insert(3, 'for_sale')
        publication.insert(4, 'chapters')
        publication.insert(5, 'cover_image')
        publication.insert(6, 'metadata_upload')
        publication.insert(7, 'owner_password')
        publication.insert(8, 'user_password')

        original['publication'] = publication

        return original
