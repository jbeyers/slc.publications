import Acquisition, os
from types import *
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.AdvancedQuery import In, Eq, Le, Ge, And, Or



class PublicationsBySubjectView(BrowserView):
    """View for displaying the publications by Subject overview page 
    """
    template = ViewPageTemplateFile('publications_by_subject.pt')
    
    def __call__(self):
        self.request.set('disable_border', True)
        
        context = Acquisition.aq_inner(self.context)
        subject = self.request.get('subject', [])
        
        portal_languages = getToolByName(context, 'portal_languages')
        preflang = portal_languages.getPreferredLanguage()
        
        portal_catalog = getToolByName(context, 'portal_catalog')
        if hasattr(portal_catalog, 'getZCatalog'):
            portal_catalog = portal_catalog.getZCatalog()
        
        PQ = Eq('portal_type', 'File') & \
             In('object_provides', 'slc.publications.interfaces.IPublicationEnhanced') & \
             In('Subject', subject) & \
             Eq('review_state', 'published') & \
             Eq('Language', preflang)
             
        PUBS = portal_catalog.evalAdvancedQuery(PQ, (('effective','desc'),) )
        
       
        publist = {}
        parentlist = []
        
        # we implement a simple sorting by folder id to have a grouping. This is not too nice yet
            
        for P in PUBS:
            path = P.getPath()
            parentpath = os.path.dirname(path)
            parentlist.append(parentpath)
            section = publist.get(parentpath, [])
            section.append(P)
            publist[parentpath] = section
            
        Q = In('portal_type', ['Folder', 'Large Plone Folder']) & \
            In('object_provides', 'slc.publications.interfaces.IPublicationContainerEnhanced')& \
            Eq('Language', preflang)
        PARENTS = portal_catalog.evalAdvancedQuery(Q, (('getObjPositionInParent','asc'),) )
        
        self.publist = publist
        self.parents = [(x.getPath(), x) for x in PARENTS]
              
        return self.template() 
        
        
        
    def subject(self):
        subject = self.request.get('subject', [])
        if type(subject) not in [ListType, TupleType]:
            subject = [subject]
            
        # XXX: implement keyword translation here
        return ", ".join([x for x in subject])
        
        