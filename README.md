thredds_crawler
===============

A simple crawler/parser for THREDDS catalogs

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
uses four regular expressions to skip lists of thousands upon thousands of individual files that are part of aggregations or FMRCs:

*  .\*files/
*  .\*Individual Files.\*
*  .\*File_Access.\*
*  .\*Forecast Model Run.\*

By setting the `skip` parameter to anything other than a superset of the default you run the risk of having some angry system admins after you.

```python
# Skipping everything!
from thredds_crawler.crawl import Crawl
c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", skip=[".*"])
assert len(c.datasets) == 0
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

## Known Issues

*  Will not handle catalogs that reference themselves