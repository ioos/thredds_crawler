# import logging

from thredds_crawler.crawl import Crawl

# logger = logging.getLogger("thredds_crawler")
# logger.setLevel(logging.DEBUG)
# logger.handlers = [logging.StreamHandler()]


def test_single_dataset():
    c = Crawl(
        "https://tds.maracoos.org/thredds/catalog/REALTIME-MODIS.xml",
        select=["MODIS1"],
    )
    assert len(c.datasets) == 1
    assert c.datasets[0].id == "MODIS1"
    assert len(c.datasets[0].services) == 1
    service_names = sorted(x.get("service") for x in c.datasets[0].services)
    assert service_names == ["compound"]


def test_two_datasets():
    c = Crawl(
        "https://tds.maracoos.org/thredds/catalog/REALTIME-MODIS.xml",
        select=["MODIS1", "MODIS3"],
    )
    expected_dataset = 2
    assert len(c.datasets) == expected_dataset


def test_regex_selects():
    c = Crawl(
        "https://tds.maracoos.org/thredds/catalog/REALTIME-MODIS.xml",
        select=["MODIS[2-8]"],
    )
    expected_dataset = 2
    assert len(c.datasets) == expected_dataset


def test_regex_skips():
    skip_everything = ".*"
    c = Crawl(
        "https://tds.maracoos.org/thredds/catalog/REALTIME-MODIS.xml",
        skip=[skip_everything],
    )
    expected_dataset = 0
    assert len(c.datasets) == expected_dataset


def test_get_all_dap_links():
    c = Crawl(
        "https://tds.marine.rutgers.edu/thredds/catalog/roms/doppio/2017_da/avg/catalog.xml",
    )
    services = [s.get("url") for d in c.datasets for s in d.services if s.get("service").lower() == "opendap"]
    assert len(services) == 1


def test_dataset_size():
    c = Crawl(
        "https://tds.marine.rutgers.edu/thredds/catalog/roms/doppio/2017_da/avg/catalog.xml",
    )
    assert c.datasets[0].size


def test_unidata_parse():
    selects = [".*Best.*"]
    skips = [
        *Crawl.SKIPS,
        ".*grib2",
        ".*grib1",
        ".*GrbF.*",
        ".*ncx2",
        "Radar Data",
        "Station Data",
        "Point Feature Collections",
        "Satellite Data",
        r"Unidata NEXRAD Composites \(GINI\)",
        "Unidata case studies",
        ".*Reflectivity-[0-9]{8}",
    ]
    c = Crawl(
        "https://thredds.ucar.edu/thredds/catalog/catalog.xml",
        select=selects,
        skip=skips,
    )

    assert len(c.datasets) > 0

    isos = [(d.id, s.get("url")) for d in c.datasets for s in d.services if s.get("service").lower() == "iso"]
    assert len(isos) > 0
