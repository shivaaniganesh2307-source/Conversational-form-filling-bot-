import sys
import os
from unittest.mock import MagicMock, patch

# Setup Python module search paths
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
app_path = os.path.join(backend_path, 'app')

sys.path.insert(0, backend_path)
sys.path.insert(0, app_path)

# Mock database calls BEFORE importing main.py so connection errors never happen
with patch('db.init_tables'), patch('db.get_connection') as mock_conn:
    # Setup mock database return values so queries don't crash
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    
    import pytest
    from app.main import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client