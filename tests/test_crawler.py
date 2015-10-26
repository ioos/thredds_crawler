import unittest

from thredds_crawler.crawl import Crawl


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
        assert len(c.datasets) == 3

        # Get all DAP links:
        services = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "opendap"]
        assert len(services) == 3

    def test_regex_skips(self):
        # skip everything
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", skip=[".*"])
        assert len(c.datasets) == 0

    def test_iso_links(self):
        c = Crawl("http://thredds.axiomalaska.com/thredds/catalogs/global.html", debug=True)
        isos = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "iso"]
        assert "?dataset=" in isos[0]
        assert "&catalog=" in isos[0]

    def test_dataset_size_using_xml(self):
        c = Crawl("http://tds.maracoos.org/thredds/catalog/MODIS-Composites-1Day/2014/catalog.xml", debug=True)
        self.assertIsNotNone(c.datasets[0].size)

    def test_dataset_size_using_dap(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=["MODIS-One-Agg"], debug=True)
        self.assertIsNotNone(c.datasets[0].size)
