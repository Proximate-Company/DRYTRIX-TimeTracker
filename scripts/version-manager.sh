#!/bin/bash
# Version Manager for TimeTracker - Unix Shell Wrapper

if [ $# -eq 0 ]; then
    echo "Usage: ./version-manager.sh [action] [options]"
    echo ""
    echo "Actions:"
    echo "  tag [version] [message]  - Create a version tag"
    echo "  build [number]           - Create a build tag"
    echo "  list                     - List all tags"
    echo "  info [tag]               - Show tag information"
    echo "  status                   - Show current status"
    echo "  suggest                  - Suggest next version"
    echo ""
    echo "Examples:"
    echo "  ./version-manager.sh tag v1.2.3 'Release 1.2.3'"
    echo "  ./version-manager.sh build 123"
    echo "  ./version-manager.sh status"
    echo ""
    exit 1
fi

python3 scripts/version-manager.py "$@"
