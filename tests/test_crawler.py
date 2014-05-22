import unittest

from thredds_crawler.crawl import Crawl


class CrawlerTest(unittest.TestCase):
    def test_single_dataset(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=["MODIS-Agg"])
        assert len(c.datasets) == 1
        assert c.datasets[0].id == "MODIS-Agg"
        assert len(c.datasets[0].services) == 2
        service_names = sorted(map(lambda x: x.get('service'), c.datasets[0].services))
        assert service_names == ["ISO", "OPENDAP"]

    def test_two_datasets(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=["MODIS-Agg", "MODIS-2012-Agg"])
        assert len(c.datasets) == 2

    def test_regex_selects(self):
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", select=[".*-Agg"])
        assert len(c.datasets) == 9

        # Get all DAP links:
        services = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "opendap"]
        assert len(services) == 9

    def test_regex_skips(self):
        # skip everything
        c = Crawl("http://tds.maracoos.org/thredds/MODIS.xml", skip=[".*"])
        assert len(c.datasets) == 0

    def test_iso_links(self):
        # skip everything
        c = Crawl("http://thredds.axiomalaska.com/thredds/catalogs/global.html", debug=True)
        isos = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "iso"]
        assert "?dataset=" in isos[0]
        assert "&catalog=" in isos[0]
