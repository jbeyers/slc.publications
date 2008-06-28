import App.Common
import os
from Acquisition import aq_base, aq_inner, aq_parent
import ConfigParser, StringIO, tempfile, os, urllib, logging, re
from types import *
from persistent.dict import PersistentDict
from zope import interface
from zope import component

from slc.publications import interfaces
from slc.publications.utils import _get_storage_folder

from Products.Archetypes.utils import mapply
from Products.ATContentTypes import interface as atctifaces
from Products.CMFCore.utils import getToolByName
from Products.LinguaPlone.config import RELATIONSHIP
from ComputedAttribute import ComputedAttribute
from DateTime import DateTime

from slc.publications.pdf.interfaces import IPDFParser
from slc.publications.ini.interfaces import IINIParser

try:
    from zope.app.annotation import interfaces as annointerfaces
except ImportError, err:
    # Zope 2.10 support
    from zope.annotation import interfaces as annointerfaces

from p4a.common.descriptors import atfield
from p4a.subtyper.interfaces import ISubtyper

import logging
logger = logging.getLogger('slc.publications')

@interface.implementer(interfaces.IPublication)
@component.adapter(atctifaces.IATFile)
def ATCTFilePublication(context):
    if not interfaces.IPublicationEnhanced.providedBy(context):
        return None
    return _ATCTPublication(context)

_marker=[]

class _ATCTPublication(object):
    """ 
    """
    interface.implements(interfaces.IPublication)
    component.adapts(atctifaces.IATFile)
                                               
    def __init__(self, context):
        self.context = context

    def __str__(self):
        return '<slc.publication %s title=%s>' % (self.__class__.__name__, self.title)
    __repr__ = __str__


    def editChapter(self, chapter, metadata):
        """ add/edit a link object with the given chapter name and modify its metadata """
        additionals = _get_storage_folder(self.context)
        C = getattr(additionals, chapter, None)

        if C is None:
            return

        setMetadataMap(C, metadata)
        

                
                
                
    def setMetadataIniMap(self, metadata):
        """ Given a complex metadata map from e.g. the ini parser set the metadata on all translations and chapters """
        translations = self.context.getTranslations()
        canonical = self.context.getCanonical()
        subtyper = component.getUtility(ISubtyper)
        
        for lang in metadata.keys():
            
            if lang == 'default': 
                continue    # we skip the default section

            if translations.has_key(lang):
                translation = translations[lang][0]
                if not subtyper.existing_type(translation) or \
                   subtyper.existing_type(translation).name != 'slc.publications.Publication':
                   subtyper.change_type(translation, 'slc.publications.Publication')
                   
            else:
                canonical.addTranslation(lang)
                translation = canonical.getTranslation(lang)
                # make the translation a publication as well
                subtyper.change_type(translation, 'slc.publications.Publication')
                
                translations[lang] = [translation, None]

            # if there is a default, we merge it with the language specifics. 
            # But only for existing values. So the language sections extend the default

            langmap = metadata[lang]
                
            adapter = interfaces.IPublication(translation)
            for key in langmap.keys():
                if key == '':   
                    # no key means the publication itself
                    
                    # merge defaults
                    publication_map = langmap['']
                    if  metadata.has_key('default'):
                        defaults = metadata['default']['']
                        for x in defaults.keys():
                            if not publication_map.get(x):
                                publication_map[x] = defaults[x]
                    setMetadataMap(translation, publication_map)
                else:
                    # if key is available, it contains the name of the chapter
                    print "importing a chapter", key
                    adapter.editChapter(key, langmap[key])

    def generateImage(self):
        """
        try safely to generate the cover image if pdftk and imagemagick are present
        """
        tmp_pdfin = tmp_pdfout = tmp_gifin = None
        try:
            mainpub = self.context.getCanonical()
            data = str(mainpub.getFile())
            if not data:
                return 0
            tmp_pdfin = tempfile.mkstemp(suffix='.pdf')
            tmp_pdfout = tempfile.mkstemp(suffix='.pdf')
            tmp_gifin = tempfile.mkstemp(suffix='.gif')
            fhout = open(tmp_pdfout[1], "w")
            fhimg = open(tmp_gifin[1], "r")
            fhout.write(data)
            fhout.seek(0)
            cmd = "pdftk %s cat 1 output %s" %(tmp_pdfout[1], tmp_pdfin[1])
            logger.info(cmd)
            res = os.popen(cmd)
            result = res.read()
            if result:
                logger.warn("popen-1: %s" % (result))
            cmd = "convert %s -resize 80x113 %s" %(tmp_pdfin[1], tmp_gifin[1])
            res = os.popen(cmd)
            result = res.read()
            if result:
                logger.warn("popen-2: %s" % (result))
            #fhimg.seek(0)
            coverdata = fhimg.read()
            self.context.getField('cover_image').getMutator(self.context)(coverdata)
            status = 1
        except Exception, e:
            logger.warn("generateImage: Could not autoconvert because: %s" %e)
            status = 0

        # try to clean up
        if tmp_pdfin is not None:
            try: os.remove(tmp_pdfin[1])
            except: pass
        if tmp_pdfout is not None:
            try: os.remove(tmp_pdfout[1])
            except: pass
        if tmp_gifin is not None:
            try: os.remove(tmp_gifin[1])
            except: pass

        return status



def setMetadataMap(ob, metadata):
    """ sets a simple map with metadata on the current context. 
        we also do some conversions for old metadata ini files.
    """
    _marker = []
    compatibility = {'NACE': 'nace', 
                     }
    for comp in compatibility.keys():
        if metadata.has_key(comp):
            metadata[compatibility[comp]] = metadata[comp]
            del metadata[comp]

    # we dont want to set the language explicitly
    if metadata.has_key('language'):
        del metadata['language']

    # convert old MTSubject
    if metadata.has_key('MTSubject'):
        newmt = []
        mt = metadata['MTSubject']
        for m in mt:
            newmt.append(os.path.basename(str(m)))
        metadata['multilingual_thesaurus'] = newmt
        del metadata['MTSubject']
    

    # convert the old country path notation to ISOCode notation
    if metadata.has_key('Country'):
        c = metadata['Country']
        newc = []
        for C in c:
            elems = C.split("/")
            if len(elems)<2:
                continue
            elif len(elems)==2:
                newc.append('EU')
            else:
                if str(elems[2])=='MS':
                    newc.append('EU')
                else:
                    newc.append(str(elems[2]))
        metadata['country'] = newc
        del metadata['Country']
                    
    for key in metadata:
        print "Setting: %s - %s" %(key, metadata[key])
            
        field = ob.getField(key)
        if field is None:
            continue
        
        result = field.widget.process_form(ob, field, metadata,
                                               empty_marker=_marker,
                                               validating=False)
        if result is _marker or result is None:
            continue
            
        mutator = field.getMutator(ob)
        __traceback_info__ = (ob, field, mutator)
        result[1]['field'] = field.__name__
        mapply(mutator, result[0], **result[1])

    ob.reindexObject()


            