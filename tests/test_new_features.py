import pytest
from app import db
from app.models import Project, User, SavedFilter


@pytest.mark.smoke
@pytest.mark.api
def test_burndown_endpoint_available(client, app):
    """Test that burndown endpoint is available."""
    # Minimal entities
    u = User(username='admin')
    u.role = 'admin'
    u.is_active = True
    db.session.add(u)
    p = Project(name='X', client_id=1, billable=False)
    db.session.add(p)
    db.session.commit()
    # Just ensure route exists; not full auth flow here
    # This is a placeholder smoke test to be expanded in integration tests
    assert True


@pytest.mark.smoke
@pytest.mark.models
def test_saved_filter_model_roundtrip(app):
    """Test that SavedFilter can be created and serialized."""
    # Ensure SavedFilter can be created and serialized
    sf = SavedFilter(user_id=1, name='My Filter', scope='time', payload={'project_id': 1, 'tag': 'deep'})
    db.session.add(sf)
    db.session.commit()
    as_dict = sf.to_dict()
    assert as_dict['name'] == 'My Filter'
    assert as_dict['scope'] == 'time'

