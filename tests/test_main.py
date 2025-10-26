def test_read_main_root(client):
    """
    Testing basic root `/` connectivity. The app does not have
    a root path, so it returns 404, but since it returns it's
    working.
    """
    response = client.get("/")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_cors_allowed_origin(client):
    """
    Testing cors for allowed origins.
    """
    headers = {"Origin": "http://localhost:3000"}
    response = client.get("/docs", headers=headers)

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_disallowed_origin(client):
    """
    Testing cors for disallowed origins.
    """
    headers = {"Origin": "https://www.google.com"}
    response = client.get("/docs", headers=headers)

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_request(client):
    """
    Testing more specifically the cors preflight
    response.
    """
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Token, Content-Type",
    }

    response = client.options("/docs", headers=headers)

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers
    assert "GET" in response.headers["access-control-allow-methods"]
    assert "X-Token" in response.headers["access-control-allow-headers"]


def test_openapi_meta_info(client):
    """
    Test that the openapi.json endpoint contains the correct
    meta-information set in the FastAPI constructor.
    """
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert "info" in schema
    assert schema["info"]["title"] == "Open Forum"
    assert schema["info"]["version"] == "0.1.0"
