from thredds_crawler.etree import etree
import urlparse
import requests
import os
import re
from thredds_crawler.utils import construct_url

INV_NS = "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
XLINK_NS = "http://www.w3.org/1999/xlink"

class Crawl(object):

    def __init__(self, catalog_url, select=None, skip=None):
        """
        select: a list of dataset IDs. Python regex supported.
        skip:   list of dataset names and/or a catalogRef titles.  Python regex supported.
        """
        # Only process these dataset IDs
        if select is not None:
            select = map(lambda x: re.compile(x), select)
        self.select = select

        # Skip these dataset links, such as a list of files
        # ie. "files/"
        if skip is None:
            skip = [".*files/", ".*Individual Files.*", ".*File_Access.*", ".*Forecast Model Run.*"]
        self.skip = map(lambda x: re.compile(x), skip)

        self.datasets = [LeafDataset(url) for url in self._run(url=catalog_url)]

    def _run(self, url):
        u = urlparse.urlsplit(url)
        name, ext = os.path.splitext(u.path)
        if ext == ".html":
            u = urlparse.urlsplit(url.replace(".html",".xml"))
        url = u.geturl()
        # Get an etree object
        try:
            r = requests.get(url)
            tree = etree.XML(str(r.text))
        except BaseException:
            return

        # Crawl the catalogRefs:
        for ref in tree.findall('.//{%s}catalogRef' % INV_NS):
            # Check skips
            title = ref.get("{%s}title" % XLINK_NS)
            if not any([x.match(title) for x in self.skip]):
                for ds in self._run(url=construct_url(url, ref.get("{%s}href" % XLINK_NS))):
                    yield ds

        # Get the leaf datasets
        ds = []
        for leaf in tree.findall('.//{%s}dataset[@urlPath]' % INV_NS):
            # Subset by the skips
            name = leaf.get("name")
            if any([x.match(name) for x in self.skip]):
                break

            # Subset by the Selects defined
            if self.select is not None:
                gid = leaf.get('ID')
                if any([x.match(gid) for x in self.select]):
                    yield "%s?dataset=%s" % (url, gid)
            else:
                yield "%s?dataset=%s" % (url, leaf.get('ID'))        

class LeafDataset(object):
    def __init__(self, dataset_url):
        # Get an etree object
        r = requests.get(dataset_url)
        tree = etree.XML(str(r.text))

        dataset = tree.find("{%s}dataset" % INV_NS)
        self.id = dataset.get("ID")
        self.name = dataset.get("name")
        self.metadata = dataset.find("{%s}metadata" % INV_NS)
        service_tag = dataset.find("{%s}serviceName" % INV_NS)
        if service_tag is None:
            service_tag = self.metadata.find("{%s}serviceName" % INV_NS)
        service_name = service_tag.text

        self.services = []
        for service in tree.findall(".//{%s}service[@name='%s']" % (INV_NS, service_name)):
            if service.get("serviceType") == "Compound":
                for s in service.findall("{%s}service" % INV_NS):
                    url = construct_url(dataset_url, s.get('base')) + dataset.get("urlPath")
                    if s.get("suffix") is not None:
                        url += s.get("suffix")
                    self.services.append( {'name' : s.get('name'), 'service' : s.get('serviceType'), 'url' : url } )
            else:
                url = construct_url(dataset_url, service.get('base')) + dataset.get("urlPath") + service.get("suffix")
                self.services.append( {'name' : service.get('name'), 'service' : service.get('serviceType'), 'url' : url } )


