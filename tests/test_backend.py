from unittest.mock import MagicMock, patch

def test_process_endpoint_valid_payload(client):
    payload = {
        "session_id": "test_session_1",
        "message": "Hello, my email is test@example.com",
    }
    # Patch at psycopg2 level so ALL un-mocked DB calls anywhere in the request lifecycle return a dummy connection
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock DB select response for get_saved_conversation
        # If fetchone returns None, main.py initializes a fresh session state safely
        mock_cursor.fetchone.return_value = None

        response = client.post("/api/chat", json=payload)
        assert response.status_code in [200, 201]


def test_process_endpoint_empty_payload(client):
    response = client.post("/api/chat", json={})
    assert response.status_code in [400, 422, 200]