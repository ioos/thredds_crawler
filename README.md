thredds_crawler
===============

A simple crawler/parser for THREDDS catalogs

Installation
------------

thredds_crawler is available on pypi and is easiest installed using `pip`.

```bash
pip install thredds_crawler
```
`lxml` and `requests` will be installed automatically


Usage
------

### Select

You can select datasets based on their THREDDS ID using the 'select' parameter.  Python regex is supported.


```python
> from thredds_crawler.crawl import Crawl
> c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"])
> print c.datasets
[
  <LeafDataset id: MODIS-Agg, name: MODIS-Complete Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2009-Agg, name: MODIS-2009 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2010-Agg, name: MODIS-2010 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2011-Agg, name: MODIS-2011 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2012-Agg, name: MODIS-2012 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2013-Agg, name: MODIS-2013 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-One-Agg, name: 1-Day-Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-Three-Agg, name: 3-Day-Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-Seven-Agg, name: 7-Day-Aggregation, services: ['OPENDAP', 'ISO']>
]
```

### Skip

You can skip datasets based on their `name` and catalogRefs based on their `xlink:title`.  By default, the crawler
uses some common regular expressions to skip lists of thousands upon thousands of individual files that are part of aggregations or FMRCs:

*  `.*files.*`
*  `.*Individual Files.*`
*  `.*File_Access.*`
*  `.*Forecast Model Run.*`
*  `.*Constant Forecast Offset.*`
*  `.*Constant Forecast Date.*`

By setting the `skip` parameter to anything other than a superset of the default you run the risk of having some angry system admins after you.

You can access the default `skip` list through the Crawl.SKIPS class variable
```python
> from thredds_crawler.crawl import Crawl
> print Crawl.SKIPS
[
  '.*files.*',
  '.*Individual Files.*',
  '.*File_Access.*',
  '.*Forecast Model Run.*',
  '.*Constant Forecast Offset.*',
  '.*Constant Forecast Date.*'
]
```

If you need to remove or add a new `skip`, it is **strongly** encouraged you use the `SKIPS` class variable as a starting point!

```python
> from thredds_crawler.crawl import Crawl
> skips = Crawl.SKIPS + [".*-Day-Aggregation"]
> c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"], skip=skips)
> print c.datasets
[
  <LeafDataset id: MODIS-Agg, name: MODIS-Complete Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2009-Agg, name: MODIS-2009 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2010-Agg, name: MODIS-2010 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2011-Agg, name: MODIS-2011 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2012-Agg, name: MODIS-2012 Aggregation, services: ['OPENDAP', 'ISO']>,
  <LeafDataset id: MODIS-2013-Agg, name: MODIS-2013 Aggregation, services: ['OPENDAP', 'ISO']>,
]
```

### Debugging

You can pass in a `debug=True` parameter to Crawl to log to STDOUT what is actually happening.

```python
> from thredds_crawler.crawl import Crawl
> skips = Crawl.SKIPS + [".*-Day-Aggregation"]
>>> c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"], skip=skips, debug=True)
Crawling: http://tds.maracoos.org/thredds/MODIS.xml
Skipping catalogRef based on 'skips'.  Title: MODIS Individual Files
Skipping catalogRef based on 'skips'.  Title: 1-Day Individual Files
Skipping catalogRef based on 'skips'.  Title: 3-Day Individual Files
Skipping catalogRef based on 'skips'.  Title: 8-Day Individual Files
Processing MODIS-Agg
Processing MODIS-2009-Agg
Processing MODIS-2010-Agg
Processing MODIS-2011-Agg
Processing MODIS-2012-Agg
Processing MODIS-2013-Agg
Skipping dataset based on 'skips'.  Name: 1-Day-Aggregation
```


### Logging

If you are using `thredds_crawler` from inside of another program, you can access its logs
using the named logger `thredds_crawler` to control the log level.  If you access to the named
logger, **do not** include `debug=True` when initializing the Crawl object.

```python
import logging
crawl_log = logging.getLogger('thredds_crawler')
crawl_log.setLevel(logging.WARNING)
```


## Dataset

You can get some basic information about a LeafDataset, including the services available.

```python
> from thredds_crawler.crawl import Crawl
> c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"])
> dataset = c.datasets[0]
> print dataset.id
MODIS-Agg
> print dataset.name
MODIS-Complete Aggregation
> print dataset.services
[
  {
    'url': 'http://tds.maracoos.org/thredds/dodsC/MODIS-Agg.nc',
    'name': 'odap',
    'service': 'OPENDAP'
  },
  {
    'url': 'http://tds.maracoos.org/thredds/iso/MODIS-Agg.nc',
    'name': 'iso',
    'service': 'ISO'
  }
]
```

If you have a list of datasets you can easily return all endpoints of a certain type:
```python
> from thredds_crawler.crawl import Crawl
> c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"])
> urls = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "opendap"]
> print urls
[
  'http://tds.maracoos.org/thredds/dodsC/MODIS-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-2009-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-2010-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-2011-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-2012-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-2013-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-One-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-Three-Agg.nc',
  'http://tds.maracoos.org/thredds/dodsC/MODIS-Seven-Agg.nc'
]
```

## Metadata

The entire THREDDS catalog metadata record is saved along with the dataset object.  It is an etree Element object ready for you to pull information out of.  See the [THREDDS metadata spec](http://www.unidata.ucar.edu/projects/THREDDS/tech/catalog/v1.0.2/InvCatalogSpec.html#metadata)

```python
> from thredds_crawler.crawl import Crawl
> c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"])
> dataset = c.datasets[0]
> print dataset.metadata.find("{http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0}documentation").text
Ocean Color data are provided as a service to the broader community, and can be
influenced by sensor degradation and or algorithm changes. We make efforts to keep
this dataset updated and calibrated. The products in these files are experimental.
Aggregations are simple means of available data over the specified time frame. Use at
your own discretion.
```


## Use Case

Below is a python script that can be used to harvest THEDDS catalogs and save the ISO metadata files
to a local directory

```python
import os
import urllib
from thredds_crawler.crawl import Crawl

import logging
import logging.handlers
logger = logging.getLogger('thredds_crawler')
fh = logging.handlers.RotatingFileHandler('/var/log/iso_harvest/iso_harvest.log', maxBytes=1024*1024*10, backupCount=5)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

SAVE_DIR="/srv/http/iso"

THREDDS_SERVERS = {
    "aoos":      "http://thredds.axiomalaska.com/thredds/catalogs/aoos.html",
    "cencoos":   "http://thredds.axiomalaska.com/thredds/catalogs/cencoos.html",
    "maracoos" : "http://tds.maracoos.org/thredds/catalog.html",
    "glos":      "http://tds.glos.us/thredds/catalog.html"
}

for subfolder, thredds_url in THREDDS_SERVERS.items():
  logger.info("Crawling %s (%s)" % (subfolder, thredds_url))
  crawler = Crawl(thredds_url, debug=True)
  isos = [(d.id, s.get("url")) for d in catalog.datasets for s in d.services if s.get("service").lower() == "iso"]
  filefolder = os.path.join(SAVE_DIR, subfolder)
  if not os.path.exists(filefolder)
    os.makedirs(filefolder)
  for iso in isos:
    try:
      filename = iso[0].replace("/", "_") + ".iso.xml"
      filepath = os.path.join(filefolder, filename)
      logger.info("Downloading/Saving %s" % filepath)
      urllib.urlretrieve(iso[1], filepath)
    except BaseException:
      logger.exception("Error!")
```

## Known Issues

*  Single threaded
