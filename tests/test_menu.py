from cli.menu import Menu, METRICS


def test_read_urls(tmp_path):
    p = tmp_path / "urls.txt"
    p.write_text("https://example.com/a\nhttps://example.com/b\n")
    menu = Menu(str(p))
    urls = menu.read_urls()
    assert len(urls) == 2
    assert urls[0].startswith("https://example.com")


class DummyMetric:
    def __init__(self):
        self.name = "dummy"

    def timed_calculate(self, url):
        return {"dummy": 0.5, "dummy_latency": 10}


def test_run_score_metric_monkeypatch(tmp_path, monkeypatch, capsys):
    # create a urls file
    p = tmp_path / "urls.txt"
    p.write_text("https://example.com/a\n")

    # inject a fake metric into METRICS mapping
    monkeypatch.setitem(METRICS, "9", ("dummy", DummyMetric))

    menu = Menu(str(p))
    menu.run_score_metric(None, "dummy")
    out = capsys.readouterr().out
    assert "https://example.com/a" in out
    assert "dummy" in out
