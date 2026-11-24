# tests/test_auth.py
import pytest


def test_auth_missing_token(client):
    response = client.post("/account-info", json={
        "username": 123456,
        "password": "password",
        "server": "Demo-Server"
    })
    assert response.status_code == 401
    assert response.get_json() == {"message": "Authorization exception"}


def test_auth_invalid_token(client):
    response = client.post("/account-info", headers={"token": "wrong-token"}, json={
        "username": 123456,
        "password": "password",
        "server": "Demo-Server"
    })
    assert response.status_code == 401
    assert response.get_json() == {"message": "Authorization exception"}


def test_auth_valid_token(client, auth_headers):
    response = client.post("/account-info", headers=auth_headers, json={
        "username": 123456,
        "password": "password",
        "server": "Demo-Server"
    })
    assert response.status_code == 200
