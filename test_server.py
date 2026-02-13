from server import app

def test_index_route():
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert b'<html' in response.data or b'<!DOCTYPE html' in response.data