import tools


def test_fetch_data_file_uses_s3_hostname_default(monkeypatch):
    monkeypatch.delenv("S3_HOSTNAME", raising=False)

    file_path = tools.fetch_data_file(None, "202401011200", "rprate")

    assert file_path == "s3://lake.fmi.fi/hrnwc/development/202401011200/interpolated_rprate.grib2"


def test_fetch_data_file_uses_s3_hostname_env(monkeypatch):
    monkeypatch.setenv("S3_HOSTNAME", "custom-s3.example")

    file_path = tools.fetch_data_file(None, "202401011200", "rprate")

    assert file_path == "s3://custom-s3.example/hrnwc/development/202401011200/interpolated_rprate.grib2"


def test_read_file_from_s3_uses_https_endpoint_from_hostname(monkeypatch):
    monkeypatch.setenv("S3_HOSTNAME", "custom-s3.example")
    captured = {}

    def fake_open_local(uri, s3):
        captured["uri"] = uri
        captured["s3"] = s3
        return "/tmp/fake-file"

    monkeypatch.setattr(tools.fsspec, "open_local", fake_open_local)

    result = tools.read_file_from_s3("s3://bucket/key.grib2")

    assert result == "/tmp/fake-file"
    assert captured["uri"] == "simplecache::s3://bucket/key.grib2"
    assert captured["s3"]["client_kwargs"]["endpoint_url"] == "https://custom-s3.example"


def test_read_file_from_s3_keeps_scheme_from_env(monkeypatch):
    monkeypatch.setenv("S3_HOSTNAME", "https://custom-s3.example")
    captured = {}

    def fake_open_local(uri, s3):
        captured["s3"] = s3
        return "/tmp/fake-file"

    monkeypatch.setattr(tools.fsspec, "open_local", fake_open_local)

    tools.read_file_from_s3("s3://bucket/key.grib2")

    assert captured["s3"]["client_kwargs"]["endpoint_url"] == "https://custom-s3.example"
