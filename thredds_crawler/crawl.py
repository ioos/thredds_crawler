try:
    import urlparse
    from urllib import quote_plus
except ImportError:
    from urllib import parse as urlparse
    from urllib.parse import quote_plus
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import sys
import re
import logging
from datetime import datetime
import pytz
from lxml import etree
from thredds_crawler.utils import construct_url
from dateutil.parser import parse
import multiprocessing as mp

INV_NS = "http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0"
XLINK_NS = "http://www.w3.org/1999/xlink"
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    # Python >= 2.7
    from logging import NullHandler
except ImportError:
    # Python < 2.7
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
logger = logging.getLogger(__name__)


def request_xml(url, auth=None):
    '''
    Returns an etree.XMLRoot object loaded from the url
    :param str url: URL for the resource to load as an XML
    '''
    try:
        r = requests.get(url, auth=auth, verify=False)
        return r.text.encode('utf-8')
    except BaseException:
        logger.error("Skipping %s (error parsing the XML)" % url)
    return


def make_leaf(url, auth):
    return LeafDataset(url, auth=auth)


class Crawl(object):

    SKIPS = [".*files.*", ".*Individual Files.*", ".*File_Access.*", ".*Forecast Model Run.*", ".*Constant Forecast Offset.*", ".*Constant Forecast Date.*"]

    def __init__(self, catalog_url, select=None, skip=None, before=None, after=None, debug=None, workers=None, auth=None):
        """
        :param select list: Dataset IDs. Python regex supported.
        :param list skip: Dataset names and/or a catalogRef titles. Python regex supported.
        :param requests.auth.AuthBase auth: requets auth object to use
        """
        workers = workers or 4
        self.pool = mp.Pool(processes=workers)

        if debug is True:
            logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        else:
            logger.addHandler(NullHandler())

        # Only process these dataset IDs
        if select is not None:
            select = [ re.compile(x) for x in select ]
        self.select = select

        # Skip these dataset links, such as a list of files
        # ie. "files/"
        if skip is None:
            skip = Crawl.SKIPS
        self.skip = [ re.compile(x) for x in skip ]

        # Only return datasets with a modified date greater or equal to this
        if after is not None:
            if not isinstance(after, datetime):
                raise ValueError("'after' parameter should be a datetime object")
            else:
                if after.tzinfo:
                    after = after.astimezone(pytz.utc)
                else:
                    after = after.replace(tzinfo=pytz.utc)
        self.after = after

        # Only return datasets with a modified date greater or equal to this
        if before is not None:
            if not isinstance(before, datetime):
                raise ValueError("'before' parameter should be a datetime object")
            else:
                if before.tzinfo:
                    before = before.astimezone(pytz.utc)
                else:
                    before = before.replace(tzinfo=pytz.utc)
        self.before = before

        self.visited  = []
        datasets = []
        urls = list(self._run(url=catalog_url, auth=auth))

        jobs = [self.pool.apply_async(make_leaf, args=(url, auth)) for url in urls]
        datasets = [j.get() for j in jobs]

        self.datasets = [ x for x in datasets if x.id is not None ]

        self.pool.close()
        self.pool.join()

    def _get_catalog_url(self, url):
        '''
        Returns the appropriate catalog URL by replacing html with xml in some
        cases
        :param str url: URL to the catalog
        '''
        u = urlparse.urlsplit(url)
        name, ext = os.path.splitext(u.path)
        if ext == ".html":
            u = urlparse.urlsplit(url.replace(".html", ".xml"))
        url = u.geturl()
        return url

    def _yield_leaves(self, url, tree):
        '''
        Yields a URL corresponding to a leaf dataset for each dataset described by the catalog
        :param str url: URL for the current catalog
        :param lxml.etree.Eleemnt tree: Current XML Tree
        '''
        for leaf in tree.findall('.//{%s}dataset[@urlPath]' % INV_NS):
            # Subset by the skips
            name = leaf.get("name")
            if any([x.match(name) for x in self.skip]):
                logger.info("Skipping dataset based on 'skips'.  Name: %s" % name)
                continue

            # Subset by before and after
            date_tag = leaf.find('.//{%s}date[@type="modified"]' % INV_NS)
            if date_tag is not None:
                try:
                    dt = parse(date_tag.text)
                except ValueError:
                    logger.error("Skipping dataset.Wrong date string %s " % date_tag.text)
                    continue
                else:
                    dt = dt.replace(tzinfo=pytz.utc)
                if self.after and dt < self.after:
                    continue
                if self.before and dt > self.before:
                    continue

            # Subset by the Selects defined
            gid = leaf.get('ID')
            if self.select is not None:
                if gid is not None and any([x.match(gid) for x in self.select]):
                    logger.debug("Processing %s" % gid)
                    yield "%s?dataset=%s" % (url, gid)
                else:
                    logger.info("Ignoring dataset based on 'selects'.  ID: %s" % gid)
                    continue
            else:
                logger.debug("Processing %s" % gid)
                yield "%s?dataset=%s" % (url, gid)

    def _compile_references(self, url, tree):
        '''
        Returns a list of catalog reference URLs for the current catalog
        :param str url: URL for the current catalog
        :param lxml.etree.Eleemnt tree: Current XML Tree
        '''
        references = []
        for ref in tree.findall('.//{%s}catalogRef' % INV_NS):
            # Check skips
            title = ref.get("{%s}title" % XLINK_NS)
            if any([x.match(title) for x in self.skip]):
                logger.info("Skipping catalogRef based on 'skips'.  Title: %s" % title)
                continue
            references.append(construct_url(url, ref.get("{%s}href" % XLINK_NS)))
        return references

    def _run(self, url, auth):
        '''
        Performs a multiprocess depth-first-search of the catalog references
        and yields a URL for each leaf dataset found
        :param str url: URL for the current catalog
        :param requests.auth.AuthBase auth: requets auth object to use
        '''
        if url in self.visited:
            logger.debug("Skipping %s (already crawled)" % url)
            return
        self.visited.append(url)

        logger.info("Crawling: %s" % url)
        url = self._get_catalog_url(url)

        # Get an etree object
        xml_content = request_xml(url, auth)
        for ds in self._build_catalog(url, xml_content):
            yield ds

    def _build_catalog(self, url, xml_content):
        '''
        Recursive function to perform the DFS and yield the leaf datasets
        :param str url: URL for the current catalog
        :param str xml_content: XML Body returned from HTTP Request
        '''
        try:
            tree = etree.XML(xml_content)
        except:
            return

        # Get a list of URLs
        references = self._compile_references(url, tree)
        # Using multiple processes, make HTTP requests for each child catalog
        jobs = [self.pool.apply_async(request_xml, args=(ref,)) for ref in references]
        responses = [j.get() for j in jobs]

        # This is essentially the graph traversal step
        for i, response in enumerate(responses):
            for ds in self._build_catalog(references[i], response):
                yield ds

        # Yield the leaves
        for ds in self._yield_leaves(url, tree):
            yield ds


class LeafDataset(object):
    def __init__(self, dataset_url, auth=None):

        self.services    = []
        self.id          = None
        self.name        = None
        self.metadata    = None
        self.catalog_url = None
        self.data_size   = None

        # Get an etree object
        r = requests.get(dataset_url, auth=auth, verify=False)
        try:
            tree = etree.XML(r.text.encode('utf-8'))
        except etree.XMLSyntaxError:
            logger.error("Error procesing %s, invalid XML" % dataset_url)
        else:
            try:
                dataset = tree.find("{%s}dataset" % INV_NS)
                self.id = dataset.get("ID")
                self.name = dataset.get("name")
                self.metadata = dataset.find("{%s}metadata" % INV_NS)
                self.catalog_url = dataset_url.split("?")[0]

                # Data Size - http://www.unidata.ucar.edu/software/thredds/current/tds/catalog/InvCatalogSpec.html#dataSize
                data_size = dataset.find("{%s}dataSize" % INV_NS)
                if data_size is not None:
                    self.data_size = float(data_size.text)
                    data_units = data_size.get('units')
                    # Convert to MB
                    if data_units == "bytes":
                        self.data_size *= 1e-6
                    elif data_units == "Kbytes":
                        self.data_size *= 0.001
                    elif data_units == "Gbytes":
                        self.data_size /= 0.001
                    elif data_units == "Tbytes":
                        self.data_size /= 1e-6

                # Services
                service_tag = dataset.find("{%s}serviceName" % INV_NS)
                if service_tag is None:
                    service_tag = self.metadata.find("{%s}serviceName" % INV_NS)
                    if service_tag is None:
                        raise ValueError("No serviceName definition found!")
                service_name = service_tag.text

                for service in tree.findall(".//{%s}service[@name='%s']" % (INV_NS, service_name)):
                    if service.get("serviceType") == "Compound":
                        for s in service.findall("{%s}service" % INV_NS):
                            url = construct_url(dataset_url, s.get('base')) + dataset.get("urlPath")
                            if s.get("suffix") is not None:
                                url += s.get("suffix")
                            # ISO like services need additional parameters
                            if s.get('name') in ["iso", "ncml", "uddc"]:
                                url += "?dataset=%s&catalog=%s" % (self.id, quote_plus(self.catalog_url))
                            self.services.append( {'name' : s.get('name'), 'service' : s.get('serviceType'), 'url' : url } )
                    else:
                        url = construct_url(dataset_url, service.get('base')) + dataset.get("urlPath") + service.get("suffix", "")
                        # ISO like services need additional parameters
                        if service.get('name') in ["iso", "ncml", "uddc"]:
                            url += "?dataset=%s&catalog=%s" % (self.id, quote_plus(self.catalog_url))
                        self.services.append( {'name' : service.get('name'), 'service' : service.get('serviceType'), 'url' : url } )
            except BaseException as e:
                logger.error('Could not process {}. {}.'.format(dataset_url, e))

    @property
    def size(self):
        if self.data_size is not None:
            return self.data_size
        try:
            dap_endpoint = next(s.get("url") for s in self.services if s.get("service").lower() == "opendap")
            # Get sizes from DDS
            try:
                import netCDF4
                nc = netCDF4.Dataset(dap_endpoint)
                bites = 0
                for vname in nc.variables:
                    var = nc.variables.get(vname)
                    bites += var.dtype.itemsize * var.size
                return bites * 1e-6  # Megabytes
            except ImportError:
                logger.error("The python-netcdf4 library is required for computing the size of this dataset.")
                return None
        except StopIteration:
            return None  # We can't calculate

    def __repr__(self):
        return "<LeafDataset id: %s, name: %s, services: %s>" % (self.id, self.name, str([s.get("service") for s in self.services]))
