import tempfile, logging, os, re
from types import *
from interfaces import IPDFParser
from zope import interface
from zope import component
from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('slc.publications.pdf')

class PDFParser(object):
    """ parses metadata from pdf files """

    interface.implements(IPDFParser)
    
    def parse(self, pdf, owner_password='', user_password=''):
        """ parses the given pdf file and returns a mapping of attributes """
        
        # This will store the parsed metadata
        META_MAP = {}
      
        statement = "pdfinfo -meta"
        if owner_password !="":
            statement += ' -opw ' + owner_password
        if user_password !="":
            statement += ' -upw ' + user_password

        # pdfinfo needs to work on a file. Write the file and start pdfinfo
        tmp_pdf = tempfile.mkstemp(suffix='.pdf')
        fd = open(tmp_pdf[1], 'w')
        fd.write( str(pdf) )
        fd.close()

        statement += ' '+tmp_pdf[1]
        logger.debug('pdfinfo commandline: %s' % statement)
        ph = os.popen4( statement )

        # get the result
        result = ph[1].read()
        logger.debug('metadata extracted by pdfinfo :\n--------------------------------\n%s ' % result)

        ph[0].close()
        ph[1].close()
        
        # cleanup the tempfile
        os.remove(tmp_pdf[1])

        # check for errors or encryption
        if result.startswith('Error'):
            error =  result.split('\n')[0]
            logger.error("Error in pdfinfo conversion: %s" % error)
            print error
            return False
            
        crypt_patt = re.compile('Encrypted:.*?copy:no', re.I)
        mobj = crypt_patt.search(result, 1)
        if mobj is not None:
            error = "Error: PDF is encrypted"
            logger.error(error)
            print result
            return False
            
        # Everything seems fine, parse the metadata
        # Caution: do not use the metalist, it's not unicode!
        # Note that pdfinfo returns a ini style list and an xml version.
        METADATA = result.split('Metadata:')
        if len(METADATA)>1:
            metalist, metaxml = METADATA
        else:
            metalist, metaxml = (result, '')


        # Hooray, metadata in the list part is not the same as the metadata in xml. Uff.
        # But metalist may not be unicode. Lets get it anyway..

#        list_map = {}
#        for line in metalist.split("\n"):
#            elems = line.split(":")
#            if len (elems)>1:
#                k = elems[0].strip()
#                v = ":".join(elems[1:]).strip()
#            else:
#                continue                
#            list_map[k] = v
            
            
        # Get metadata out of the xml-part
        # XXX: There is probably a proper definition what to expect here. 
        # If would be a good idea to make this generic
        # It even would be smart to use an xml parser here.
        patt_list = []
        patt_list.append( ('Keywords', "<pdf:Keywords>(.*?)</pdf:Keywords>") )
        patt_list.append( ('Keywords', "pdf:Keywords='(.*?)'") )
        patt_list.append( ('Language', "<pdf:Language>(.*?)</pdf:Language>") )
        patt_list.append( ('Language', "pdf:Language='(.*?)'") )
        patt_list.append( ('UUID', "xapMM:DocumentID='uuid:(.*?)'") )
        patt_list.append( ('UUID', 'rdf:about="uuid:(.*?)"') )
        patt_list.append( ('CreationDate', "xap:CreateDate='(.*?)'") )
        patt_list.append( ('CreationDate', "<xap:CreateDate>(.*?)</xap:CreateDate>") )
        patt_list.append( ('ModificationDate', "xap:ModifyDate='(.*?)'") )
        patt_list.append( ('ModificationDate', "<xap:ModifyDate>(.*?)</xap:ModifyDate>") )
        patt_list.append( ('MetadataDate', "xap:MetadataDate='(.*?)'") )
        patt_list.append( ('MetadataDate', "<xap:MetadataDate>(.*?)</xap:MetadataDate>") )
        patt_list.append( ('Rights Webstatement', "<xapRights:WebStatement>(.*?)</xapRights:WebStatement>") )
        patt_list.append( ('Producer', "<pdf:Producer>(.*?)</pdf:Producer>") )
        patt_list.append( ('CreatorTool', "<xap:CreatorTool>(.*?)</xap:CreatorTool>") )
        patt_list.append( ('Title', "<dc:title>(.*?)</dc:title>") )
        patt_list.append( ('Description', "<dc:description>(.*?)</dc:description>") )
        patt_list.append( ('Rights', "<dc:rights>(.*?)</dc:rights>") )
        patt_list.append( ('Format', "<dc:format>(.*?)</dc:format>") )
        patt_list.append( ('Creator', "<dc:creator>(.*?)</dc:creator>") )
        patt_list.append( ('OPOCE', "pdfx:OPOCE='(.*?)'") )
        patt_list.append( ('OPOCE', "<pdfx:OPOCE>(.*?)</pdfx:OPOCE>") )

        for patt in patt_list:
            pobj = re.compile(patt[1], re.I | re.S)
            mobj = pobj.search(metaxml, 1)
            if mobj is not None:
                value = re.sub('<.*?>', '', mobj.group(1))
                META_MAP[patt[0].strip().lower()] = value.strip()
            else:
                logger.debug("No matches for "+ str(patt[1]))


        # Get the user-defined meta-data
        add_patt = re.compile("pdfx:(.*?)='(.*?)'", re.I|re.S)

        for name, value in add_patt.findall(metaxml):
            META_MAP[name.strip().lower()] = value

        # And another format
        add_patt = re.compile("pdfx:(.*?)>(.*?)</pdfx:", re.I|re.S)
        for name, value in add_patt.findall(metaxml):
            META_MAP[name.strip().lower()] = value

        # make the author and subject to a tuple of values
        if type(META_MAP.get('author', '')) != TupleType:
            kw = META_MAP.get('author', '').split(";")
            META_MAP['author'] = tuple([x.strip() for x in kw])

        if type(META_MAP.get('keywords', '')) != TupleType:
            kw = META_MAP.get('keywords', '').split(";")
            META_MAP['keywords'] = tuple([x.strip() for x in kw])

#        for key in META_MAP:
#            meta_data = META_MAP[key]
#            if not meta_data:
#                continue
#            # use the appropriate dublin-core mutators
#            if key.upper() == "TITLE":
#                if not (self.getTitle() and meta_data ==''):
#                    self.setTitle(meta_data)
#            elif key.upper() in ["SUBJECT", "KEYWORDS"]:
#                self.setSubject(meta_data)
#            elif key.upper() == "DESCRIPTION":
#                self.setDescription(meta_data)
#            elif key.upper() == "CONTRIBUTORS":
#                self.setContributors(meta_data)
#            elif key.upper() in ("MODIFICATION_DATE", "MODIFICATIONDATE"):
#                self.setModificationDate(meta_data)
#            elif key.upper() in ("EXPIRATION_DATE", "EXPIRATIONDATE"):
#                self.setExpirationDate(meta_data)
#            elif key.upper() == "EFFECTIVE_DATE":
#                self.setEffectiveDate(meta_data)
#            elif key.upper() == "RIGHTS":
#                self.setRights(meta_data)
#            elif key.upper() == "PUBLISHER":
#                self.setPublisher(meta_data)
#            elif key.upper() == "LANGUAGE":
#                if not self.Language():
#                    self.setLanguage(meta_data)
#            elif key.upper() == "FORMAT":
#                self.setFormat(meta_data)
#            elif key.upper() == "OPOCE":
#                self.context.setOrder_id(meta_data)
    
        # If the language is given in the filename extension, we consider that as 
        # most explicit
        
        l = self._guessLanguage(pdf)
        if l and not META_MAP.has_key('language'):
            META_MAP['language'] = l
        
        return META_MAP
        

    def _guessLanguage(self, file):
        """
        try to find a language abbreviation in the string
        acceptable is a two letter language abbreviation at the start of the string followed by an _
        or at the end of the string prefixed by an _ just before the extension
        """
        if hasattr(file, 'filename'):
            filename = file.filename
        elif hasattr(file, 'id'):
            filename = file.id
        elif hasattr(file, 'getId'):
            filename = file.getId
        else:
            return None

        if callable(filename):
            filename = filename()            
                    
        def findAbbrev(id):
            if len(id)>3 and id[2] in ['_', '-']:
                lang = id[0:2].lower()
                if lang in langs:
                    return lang
            if len(id)>3 and '.' in id:
                elems = id.split('.')
                filename = ".".join(elems[:-1])
                if len(filename)>3 and filename[-3] in ['_', '-']:
                    lang = filename[-2:].strip()
                    if lang in langs:
                        return lang
                elif len(filename)==2:
                    lang = filename
                    if lang in langs:
                        return lang


        site = getSite()
        portal_languages = getToolByName(site, 'portal_languages')
        langs = portal_languages.getSupportedLanguages()

        langbyfileid = findAbbrev(filename)
        if langbyfileid in langs:
            return langbyfileid

        return ''        