# CI/CD Pipeline

## 🚀 Automated Testing & Deployment

TimeTracker includes a comprehensive CI/CD pipeline that automates testing, building, and deployment.

### Features

✅ **Multi-level Testing** - Smoke, unit, integration, security, and database tests  
✅ **Parallel Execution** - Fast feedback with parallel test jobs  
✅ **Multi-platform Builds** - AMD64 and ARM64 Docker images  
✅ **Automated Releases** - Semantic versioning and GitHub releases  
✅ **Security Scanning** - Bandit and Safety vulnerability checks  
✅ **Code Quality** - Black, Flake8, and isort validation  

### Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt -r requirements-test.txt

# Run tests
pytest -m smoke    # Quick smoke tests (< 1 min)
pytest -m unit     # Unit tests (2-5 min)
pytest             # Full test suite (15-30 min)
```

### Docker Images

Development builds are automatically published to GitHub Container Registry:

```bash
# Pull latest development build
docker pull ghcr.io/{owner}/{repo}:develop

# Pull stable release
docker pull ghcr.io/{owner}/{repo}:latest

# Run container
docker run -p 8080:8080 ghcr.io/{owner}/{repo}:latest
```

### Creating Releases

Releases are automatically created when you push to main or create a version tag:

```bash
# Create a release
git tag v1.2.3
git push origin v1.2.3

# Or merge to main
git checkout main
git merge develop
git push
```

The CI/CD pipeline will automatically:
1. Run full test suite
2. Perform security audit
3. Build multi-platform Docker images
4. Create GitHub release with deployment manifests
5. Publish to container registry

### Documentation

- **Quick Start**: [CI_CD_QUICK_START.md](CI_CD_QUICK_START.md)
- **Full Documentation**: [CI_CD_DOCUMENTATION.md](CI_CD_DOCUMENTATION.md)
- **Implementation Summary**: [CI_CD_IMPLEMENTATION_SUMMARY.md](CI_CD_IMPLEMENTATION_SUMMARY.md)

### Test Organization

Tests are organized using pytest markers:

| Marker | Purpose | Duration |
|--------|---------|----------|
| `smoke` | Critical fast tests | < 1 min |
| `unit` | Isolated component tests | 2-5 min |
| `integration` | Component interaction tests | 5-10 min |
| `security` | Security vulnerability tests | 3-5 min |
| `database` | Database tests | 5-10 min |

### CI/CD Workflows

#### Pull Requests
- Runs on: Every PR to main or develop
- Duration: ~15-20 minutes
- Tests: Smoke, unit, integration, security, database
- Quality: Code quality checks, security scanning
- Feedback: Automated PR comment with results

#### Development Builds
- Runs on: Push to develop branch
- Duration: ~25 minutes
- Output: `ghcr.io/{owner}/{repo}:develop`
- Creates: Development release with deployment manifest

#### Production Releases
- Runs on: Push to main or version tag
- Duration: ~55 minutes
- Output: `ghcr.io/{owner}/{repo}:latest`, `v1.2.3`, etc.
- Creates: GitHub release with manifests and changelog

### Monitoring

View build status and metrics:
- [GitHub Actions](../../actions)
- [Container Registry](../../pkgs/container/timetracker)
- Coverage reports (if Codecov configured)

---

**Note**: Add this section to your main README.md file

