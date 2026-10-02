# Contributing to Space Debris Tracker

Thank you for your interest in contributing! This document provides guidelines for contributing to the Space Debris Tracker project.

## Table of Contents

* [Code of Conduct](#code-of-conduct)
* [Getting Started](#getting-started)
* [How to Contribute](#how-to-contribute)
* [Development Setup](#development-setup)
* [Code Standards](#code-standards)
* [Submitting Changes](#submitting-changes)
* [Reporting Issues](#reporting-issues)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code. Be respectful, inclusive, and constructive in all interactions.

---

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Space-Debris-Project.git
   cd Space-Debris-Project
   ```
3. **Set up the development environment** (see Development Setup below)
4. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## How to Contribute

### Types of Contributions

**Bug Fixes**
- Fix broken functionality
- Improve error handling
- Resolve coordinate transformation issues

**New Features**
- Enhanced ML models
- New visualization modes
- Additional orbital filters
- API endpoints

**Documentation**
- README improvements
- Code comments
- Tutorials and examples
- API documentation

**Data Quality**
- Fix SATCAT metadata
- Improve TLE parsing
- Add missing object classifications

**Performance**
- Rendering optimizations
- Caching strategies
- WebGPU support

**Testing**
- Unit tests for backend
- Integration tests for data pipeline
- Browser compatibility testing

---

## Development Setup

### Prerequisites

- **Python 3.9+**
- **pip** for Python package management
- **Git**
- **Modern web browser** (Chrome 90+, Firefox 88+, Safari 14+)

### Backend Setup

```bash
cd webapp/
pip install -r requirements.txt
python app.py
# Server runs on http://localhost:8000
```

### Frontend Development

The frontend is a single-page application in `webapp/index.html`. To modify:

1. Edit `index.html` (inline JavaScript)
2. Refresh browser to see changes
3. Test on Chrome, Firefox, and Safari
4. Test mobile responsiveness (Chrome DevTools)

### Testing

**Manual Testing:**
```bash
cd webapp/
python app.py
# Open http://localhost:8000
# Test features interactively
```

**Unit Tests (planned):**
```bash
pytest webapp/tests/
```

---

## Code Standards

### Python

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for function signatures
- Maximum line length: 100 characters
- Docstrings for all public functions

```python
def compute_collision_risk(altitude: float, density: int) -> float:
    """
    Compute collision risk score for a satellite.

    Args:
        altitude: Orbital altitude in kilometers
        density: Number of objects within ±50 km

    Returns:
        Risk score normalized to [0, 1]
    """
    pass
```

### JavaScript

- Use ES6+ syntax (const, let, arrow functions)
- Semicolons optional but be consistent
- camelCase for variables and functions
- UPPER_CASE for constants
- Comments for complex coordinate transformations

```javascript
// Convert ECI to Three.js world coordinates
const worldPosition = eciToThreeJS(eci.x, eci.y, eci.z);
```

### Commit Messages

Use descriptive commit messages:

```
Good:
✓ "Fix: Correct LEO altitude range to 0-2000 km"
✓ "Feature: Add launch date filter to debris catalog"
✓ "Perf: Implement spatial indexing for frustum culling"

Bad:
✗ "fix bug"
✗ "update"
✗ "changes"
```

---

## Submitting Changes

### Pull Request Process

1. **Ensure code quality**
   - Code follows style guidelines
   - All tests pass
   - No console errors in browser

2. **Update documentation**
   - Add comments for complex code
   - Update README if adding features
   - Document API changes

3. **Create pull request**
   - Descriptive title and description
   - Reference related issues (#123)
   - Include screenshots for UI changes

4. **Respond to review feedback**
   - Address reviewer comments
   - Make requested changes
   - Be respectful and collaborative

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex algorithms
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or documented)
- [ ] Tested on Chrome, Firefox, and mobile
- [ ] Screenshots included (for UI changes)

---

## Reporting Issues

### Bug Reports

When reporting a bug, include:

**Environment:**
- Browser and version
- Operating system
- Device (desktop/mobile)

**Steps to Reproduce:**
1. Go to '...'
2. Click on '...'
3. Scroll to '...'
4. See error

**Expected Behavior:**
A clear description of what should happen.

**Actual Behavior:**
What actually happened (include error messages).

**Screenshots:**
If applicable, add screenshots.

### Feature Requests

For new features, describe:

- **Use Case:** What problem does this solve?
- **Proposed Solution:** How should it work?
- **Alternatives:** Other approaches considered
- **Priority:** How important is this feature?

---

## Contribution Areas

We especially welcome contributions in:

| Area | Description | Difficulty |
|------|-------------|------------|
| **ML Model** | Improve collision risk algorithm | Advanced |
| **UI/UX** | Enhance mobile experience | Intermediate |
| **Performance** | WebGPU, spatial indexing | Advanced |
| **Data Quality** | Fix SATCAT gaps | Beginner |
| **Documentation** | Tutorials, API docs | Beginner |
| **Accessibility** | Screen readers, keyboard nav | Intermediate |
| **i18n** | Translations | Beginner |
| **Testing** | Unit/integration tests | Intermediate |

---

## Questions?

- **GitHub Issues:** [Space-Debris-Project/issues](https://github.com/Guruvendra47/Space-Debris-Project/issues)
- **Email:** guruvendra47@gmail.com
- **LinkedIn:** [Guruvendra Pannu](https://www.linkedin.com/in/guruvendra-pannu)

---

**Thank you for contributing to making space debris tracking accessible to everyone!**
