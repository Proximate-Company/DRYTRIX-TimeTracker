# Task Management Feature

The Task Management feature allows you to break down projects into manageable tasks with status tracking, priority management, and time estimation.

## Features

### Core Task Management
- **Task Creation**: Create tasks with names, descriptions, priorities, and due dates
- **Status Tracking**: Track task progress through multiple states (To Do, In Progress, Review, Done, Cancelled)
- **Priority Levels**: Set priority levels (Low, Medium, High, Urgent) with visual indicators
- **Time Estimation**: Estimate hours for tasks and track actual time spent
- **Due Dates**: Set and track due dates with overdue notifications
- **Task Assignment**: Assign tasks to team members

### Integration with Time Tracking
- **Task-Specific Timers**: Start timers directly from tasks
- **Time Entry Association**: Link time entries to specific tasks
- **Progress Tracking**: Monitor progress based on estimated vs actual hours
- **Manual Time Entry**: Log time against specific tasks

### Project Organization
- **Project Breakdown**: Organize projects into logical task components
- **Task Overview**: View all tasks for a project in the project dashboard
- **Quick Actions**: Start timers, edit tasks, and manage status from project views

### User Experience
- **My Tasks**: View tasks assigned to or created by the current user
- **Overdue Tasks**: Identify and manage overdue tasks
- **Filtering & Search**: Find tasks by status, priority, project, or assignment
- **Responsive Design**: Mobile-friendly interface for task management

## Getting Started

### 1. Database Migration
If you're upgrading from a previous version, run the migration script:

```bash
cd docker
python migrate-add-tasks.py
```

### 2. Accessing Tasks
- Navigate to **Tasks** in the main navigation
- View all tasks or filter by various criteria
- Access **My Tasks** to see your assigned tasks

### 3. Creating Your First Task
1. Click **New Task** from the Tasks page
2. Select a project
3. Enter task details (name, description, priority, etc.)
4. Set estimated hours and due date
5. Assign to a team member (optional)
6. Click **Create Task**

### 4. Managing Task Status
- **Start Task**: Mark as "In Progress" when you begin working
- **Mark for Review**: Indicate when work is ready for review
- **Complete Task**: Mark as "Done" when finished
- **Cancel Task**: Mark as "Cancelled" if no longer needed

## Task Statuses

| Status | Description | Color |
|--------|-------------|-------|
| **To Do** | Task is planned but not started | Gray |
| **In Progress** | Work has begun on the task | Yellow |
| **Review** | Task is complete and ready for review | Blue |
| **Done** | Task is completed and approved | Green |
| **Cancelled** | Task is no longer needed | Gray |

## Priority Levels

| Priority | Description | Color | Use Case |
|----------|-------------|-------|----------|
| **Low** | Not urgent | Green | Nice-to-have features, documentation |
| **Medium** | Normal priority | Yellow | Standard development tasks |
| **High** | Important | Orange | Critical features, bug fixes |
| **Urgent** | Critical | Red | Production issues, security fixes |

## Time Tracking Integration

### Starting Timers from Tasks
- Click the **Timer** button on any task card
- Timer automatically associates with the task
- Track time spent on specific task components

### Manual Time Entry
- Log time against specific tasks
- Include notes and tags for better tracking
- Associate time with project and task simultaneously

### Progress Monitoring
- View estimated vs actual hours
- Track completion percentage
- Monitor task progress over time

## Project Dashboard Integration

Tasks are displayed in the project view, showing:
- Task overview with status and priority
- Quick action buttons for each task
- Progress indicators for time tracking
- Links to detailed task views

## User Permissions

- **All Users**: Can view tasks, start timers, and update status
- **Task Creators**: Can edit and delete their own tasks
- **Admins**: Can manage all tasks and view overdue reports

## Best Practices

### Task Creation
- Use clear, descriptive task names
- Break large features into smaller, manageable tasks
- Set realistic time estimates
- Assign appropriate priority levels

### Task Management
- Update status regularly as work progresses
- Use due dates to maintain project timelines
- Monitor overdue tasks and adjust priorities
- Link time entries to tasks for accurate tracking

### Project Organization
- Group related tasks under the same project
- Use consistent naming conventions
- Regular review of task status and progress
- Archive completed projects to focus on active work

## API Endpoints

The Task Management feature includes RESTful API endpoints:

- `GET /api/tasks/<task_id>` - Get task details
- `PUT /api/tasks/<task_id>/status` - Update task status
- Additional endpoints for task CRUD operations

## Mobile Support

The Task Management interface is fully responsive and optimized for mobile devices:
- Touch-friendly task cards
- Swipe gestures for quick actions
- Mobile-optimized forms and navigation
- Responsive grid layouts

## Troubleshooting

### Common Issues

**Task not appearing in project view**
- Ensure the task is assigned to the correct project
- Check that the project status is 'active'

**Timer not associating with task**
- Verify the task exists and is accessible
- Check user permissions for the task

**Overdue tasks not showing**
- Confirm due dates are set correctly
- Verify user has admin access for overdue reports

### Database Issues

If you encounter database-related errors:
1. Run the migration script: `python docker/migrate-add-tasks.py`
2. Check database connection and permissions
3. Verify all required tables exist
4. Contact system administrator if issues persist

## Future Enhancements

Planned improvements for Task Management:
- Bulk task operations (status updates, reassignment)
- Task dependencies and relationships
- Advanced reporting and analytics
- Integration with external project management tools
- Automated task scheduling and reminders
- Team collaboration features

## Support

For questions or issues with the Task Management feature:
- Check this documentation
- Review the application logs
- Contact your system administrator
- Submit feature requests through the project repository
