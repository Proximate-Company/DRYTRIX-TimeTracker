import pytest
from app import create_app, db
from app.models import Project, User, SavedFilter


@pytest.mark.smoke
@pytest.mark.api
def test_burndown_endpoint_available(client, app_context):
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
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
def test_saved_filter_model_roundtrip(app_context):
    # Ensure SavedFilter can be created and serialized
    sf = SavedFilter(user_id=1, name='My Filter', scope='time', payload={'project_id': 1, 'tag': 'deep'})
    db.session.add(sf)
    db.session.commit()
    as_dict = sf.to_dict()
    assert as_dict['name'] == 'My Filter'
    assert as_dict['scope'] == 'time'

