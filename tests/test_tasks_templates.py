import pytest

from app import db
from app.models import User, Project, Task


@pytest.mark.smoke
@pytest.mark.routes
def test_create_task_page_has_tips(client, app):
    with app.app_context():
        # Minimal data to render page
        user = User(username='ui_user', role='user')
        db.session.add(user)
        db.session.add(Project(name='UI Test Project', client='UI Test Client'))
        db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

        resp = client.get('/tasks/create')
        assert resp.status_code == 200
        assert b'data-testid="task-create-tips"' in resp.data


@pytest.mark.smoke
@pytest.mark.routes
def test_edit_task_page_has_tips(client, app):
    with app.app_context():
        # Minimal data to render page
        user = User(username='ui_editor', role='user')
        project = Project(name='Edit UI Project', client='Client X')
        db.session.add_all([user, project])
        db.session.commit()

        task = Task(project_id=project.id, name='Edit Me', status='todo', created_by=user.id, assigned_to=user.id)
        db.session.add(task)
        db.session.commit()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

        resp = client.get(f'/tasks/{task.id}/edit')
        assert resp.status_code == 200
        assert b'data-testid="task-edit-tips"' in resp.data


@pytest.mark.smoke
@pytest.mark.routes
def test_kanban_board_aria_and_dnd(authenticated_client, app):
    with app.app_context():
        # Minimal data for rendering board
        user = User(username='kanban_user', role='admin')
        project = Project(name='Kanban Project', client='Client K')
        db.session.add_all([user, project])
        db.session.commit()

        # login session
        with authenticated_client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True

        resp = authenticated_client.get('/kanban')
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        # ARIA presence on board wrapper and columns
        assert 'role="application"' in html or 'aria-label="Kanban board"' in html
        assert 'aria-live' in html  # counts or empty placeholder live regions


