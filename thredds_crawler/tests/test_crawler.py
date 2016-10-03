import unittest
from datetime import datetime, timedelta

import pytz
import logging

from thredds_crawler.crawl import Crawl
logger = logging.getLogger('thredds_crawler')
logger.setLevel(logging.DEBUG)
logger.handlers = [logging.StreamHandler()]


class CrawlerTest(unittest.TestCase):
    def test_single_dataset(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=["MODIS-One-Agg"])
        assert len(c.datasets) == 1
        assert c.datasets[0].id == "MODIS-One-Agg"
        assert len(c.datasets[0].services) == 2
        service_names = sorted(map(lambda x: x.get('service'), c.datasets[0].services))
        assert service_names == ["ISO", "OPENDAP"]

    def test_two_datasets(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=["MODIS-One-Agg", "MODIS-Three-Agg"])
        assert len(c.datasets) == 2

    def test_regex_selects(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"])
        assert len(c.datasets) == 12

        # Get all DAP links:
        services = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "opendap"]
        assert len(services) == 12

    def test_regex_skips(self):
        # skip everything
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", skip=[".*"])
        assert len(c.datasets) == 0

    def test_iso_links(self):
        c = Crawl("http://thredds.axiomdatascience.com/thredds/global.html")
        isos = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "iso"]
        assert "?dataset=" in isos[0]
        assert "&catalog=" in isos[0]

    def test_dataset_size_using_xml(self):
        c = Crawl("http://tds.maracoos.org/thredds/catalog/MODIS-Composites-1Day/2014/catalog.xml")
        self.assertIsNotNone(c.datasets[0].size)

    def test_dataset_size_using_dap(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=["MODIS-One-Agg"])
        self.assertIsNotNone(c.datasets[0].size)

    def test_modified_time(self):
        # after with timezone
        af = datetime(2015, 12, 30, 0, 0, tzinfo=pytz.utc)
        c = Crawl("http://tds.maracoos.org/thredds/catalog/MODIS-Chesapeake-Salinity/raw/2015/catalog.xml", after=af)
        assert len(c.datasets) == 3

        # after without timezone
        af = datetime(2015, 12, 30, 0, 0)
        c = Crawl("http://tds.maracoos.org/thredds/catalog/MODIS-Chesapeake-Salinity/raw/2015/catalog.xml", after=af)
        assert len(c.datasets) == 3

        # before
        bf = datetime(2016, 1, 5, 0, 0)
        c = Crawl("http://tds.maracoos.org/thredds/catalog/MODIS-Chesapeake-Salinity/raw/2016/catalog.xml", before=bf)
        assert len(c.datasets) == 3

        # both
        af = datetime(2016, 1, 20, 0, 0)
        bf = datetime(2016, 2, 1, 0, 0)
        c = Crawl("http://tds.maracoos.org/thredds/catalog/MODIS-Chesapeake-Salinity/raw/2016/catalog.xml", before=bf, after=af)
        assert len(c.datasets) == 11

    def test_ssl(self):
        c = Crawl("https://opendap.co-ops.nos.noaa.gov/thredds/catalog/NOAA/DBOFS/MODELS/201501/catalog.xml")
        assert len(c.datasets) > 0

    def test_unidata_parse(self):
        selects = [".*Best.*"]
        skips   = Crawl.SKIPS  + [".*grib2", ".*grib1", ".*GrbF.*", ".*ncx2",
                                  "Radar Data", "Station Data",
                                  "Point Feature Collections", "Satellite Data",
                                  "Unidata NEXRAD Composites \(GINI\)",
                                  "Unidata case studies",
                                  ".*Reflectivity-[0-9]{8}"]
        c = Crawl(
            'http://thredds.ucar.edu/thredds/catalog.xml',
            select=selects,
            skip=skips
        )

        assert len(c.datasets) > 0

        isos = [(d.id, s.get("url")) for d in c.datasets for s in d.services if s.get("service").lower() == "iso"]
        assert len(isos) > 0
