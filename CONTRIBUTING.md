# 🤝 Contributing to DocaCast

Thank you for your interest in contributing to DocaCast! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful**: Treat all contributors with respect and kindness
- **Be inclusive**: Welcome contributions from people of all backgrounds
- **Be collaborative**: Work together to improve the project
- **Be constructive**: Provide helpful feedback and suggestions
- **Be patient**: Remember that everyone is learning and growing

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8+ installed
- Node.js 16+ installed
- Git configured with your GitHub account
- A Google API key for testing
- An Adobe PDF Embed API client ID for frontend testing

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/your-username/DocaCast.git
   cd DocaCast
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/ironsupr/DocaCast.git
   ```

## Development Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Frontend Setup

```bash
cd frontend/pdf-reader-ui
npm install
```

### Environment Configuration

Create `.env` files as described in [INSTALLATION.md](INSTALLATION.md).

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend/pdf-reader-ui
npm test

# Linting
cd backend
flake8 .
black --check .

cd frontend/pdf-reader-ui
npm run lint
```

## Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

1. **Bug fixes**: Fixing issues in the codebase
2. **Feature additions**: Adding new functionality
3. **Documentation improvements**: Enhancing docs and examples
4. **Performance optimizations**: Making the app faster and more efficient
5. **UI/UX improvements**: Enhancing the user interface
6. **Test coverage**: Adding or improving tests
7. **Code refactoring**: Improving code quality and structure

### Before You Start

1. **Check existing issues**: Look for existing issues or discussions
2. **Create an issue**: For significant changes, create an issue first to discuss
3. **Keep it focused**: Each contribution should address a single concern
4. **Follow conventions**: Maintain consistency with existing code style

## Submitting Changes

### Branch Naming

Use descriptive branch names:

```bash
# Examples
git checkout -b feature/two-speaker-improvements
git checkout -b fix/audio-generation-timeout
git checkout -b docs/api-documentation-update
git checkout -b refactor/pdf-processing-cleanup
```

### Commit Messages

Write clear, descriptive commit messages:

```bash
# Good examples
git commit -m "feat: add support for custom TTS voice selection"
git commit -m "fix: resolve memory leak in PDF processing"
git commit -m "docs: update API documentation with new endpoints"
git commit -m "test: add unit tests for vector store operations"

# Use conventional commit format
# type(scope): description
```

### Commit Types

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Pull Request Process

1. **Update your branch**:

   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a pull request** with:

   - Clear title and description
   - Reference to related issues
   - Screenshots for UI changes
   - Test results if applicable

3. **Pull request template**:

   ```markdown
   ## Description

   Brief description of changes

   ## Type of Change

   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring

   ## Testing

   - [ ] Tests pass locally
   - [ ] Added new tests if needed
   - [ ] Manual testing completed

   ## Related Issues

   Fixes #123

   ## Screenshots (if applicable)
   ```

## Bug Reports

### Before Reporting

1. **Search existing issues**: Check if the bug is already reported
2. **Use latest version**: Ensure you're using the most recent version
3. **Reproduce the issue**: Confirm the bug is reproducible

### Bug Report Template

```markdown
## Bug Description

Clear description of the bug

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior

What should happen

## Actual Behavior

What actually happens

## Environment

- OS: [e.g., Windows 10, macOS 12]
- Python version: [e.g., 3.11]
- Node.js version: [e.g., 18.0]
- Browser: [e.g., Chrome 120]

## Additional Context

- Error messages
- Screenshots
- Log files
```

## Feature Requests

### Before Requesting

1. **Check existing requests**: Look for similar feature requests
2. **Consider alternatives**: Think about existing workarounds
3. **Scope appropriately**: Keep requests focused and achievable

### Feature Request Template

```markdown
## Feature Description

Clear description of the proposed feature

## Use Case

Why is this feature needed? What problem does it solve?

## Proposed Solution

How should this feature work?

## Alternatives Considered

What other approaches have you considered?

## Additional Context

Any additional information or context
```

## Code Style

### Python (Backend)

We use the following tools and conventions:

- **Black**: Code formatting
- **flake8**: Linting
- **isort**: Import sorting
- **mypy**: Type checking

```bash
# Format code
black .
isort .

# Check style
flake8 .
mypy .
```

#### Python Style Guidelines

```python
# Good examples
def process_pdf_document(file_path: str, options: Dict[str, Any]) -> ProcessingResult:
    """Process a PDF document and extract text content.

    Args:
        file_path: Path to the PDF file
        options: Processing options dictionary

    Returns:
        ProcessingResult containing extracted text and metadata

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ProcessingError: If PDF processing fails
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        # Processing logic here
        return ProcessingResult(text=extracted_text, metadata=metadata)
    except Exception as e:
        raise ProcessingError(f"Failed to process PDF: {e}") from e
```

### TypeScript/JavaScript (Frontend)

We use the following tools:

- **ESLint**: Linting
- **Prettier**: Code formatting
- **TypeScript**: Type checking

```bash
# Format code
npm run format

# Check style
npm run lint

# Type check
npm run type-check
```

#### TypeScript Style Guidelines

```typescript
// Good examples
interface PodcastGenerationConfig {
  filename: string;
  podcast: boolean;
  twoSpeakers: boolean;
  contentStyle?: "academic" | "casual" | "professional";
}

const generatePodcast = async (
  config: PodcastGenerationConfig
): Promise<PodcastResult> => {
  try {
    const response = await fetch("/api/generate-audio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to generate podcast:", error);
    throw error;
  }
};
```

## Testing

### Backend Testing

We use pytest for backend testing:

```python
# Example test
import pytest
from unittest.mock import Mock, patch
from processing import process_pdf

def test_process_pdf_success():
    """Test successful PDF processing."""
    # Given
    mock_pdf_path = "test_document.pdf"

    # When
    with patch('fitz.open') as mock_open:
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Sample text content"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_open.return_value = mock_doc

        result = process_pdf(mock_pdf_path)

    # Then
    assert result.text == "Sample text content"
    assert result.page_count == 1

def test_process_pdf_file_not_found():
    """Test PDF processing with missing file."""
    with pytest.raises(FileNotFoundError):
        process_pdf("nonexistent.pdf")
```

### Frontend Testing

We use React Testing Library and Jest:

```typescript
// Example test
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PodcastGenerator } from "./PodcastGenerator";

describe("PodcastGenerator", () => {
  it("should generate podcast when file is selected", async () => {
    // Given
    render(<PodcastGenerator />);
    const fileInput = screen.getByRole("button", { name: /upload/i });
    const generateButton = screen.getByRole("button", { name: /generate/i });

    // When
    const file = new File(["test content"], "test.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(generateButton);

    // Then
    await waitFor(() => {
      expect(screen.getByText(/generating/i)).toBeInTheDocument();
    });
  });
});
```

### Test Coverage

Maintain good test coverage:

- **Backend**: Aim for >80% coverage
- **Frontend**: Aim for >70% coverage for components
- **Critical paths**: 100% coverage for core functionality

```bash
# Check coverage
cd backend
pytest --cov=. --cov-report=html

cd frontend/pdf-reader-ui
npm run test -- --coverage
```

## Documentation

### Types of Documentation

1. **Code comments**: Explain complex logic and algorithms
2. **API documentation**: Document all endpoints and parameters
3. **User guides**: Help users understand how to use features
4. **Developer guides**: Help contributors understand the codebase

### Documentation Standards

- **Clear and concise**: Use simple language
- **Up-to-date**: Keep docs synchronized with code changes
- **Examples included**: Provide practical examples
- **Well-structured**: Use consistent formatting and organization

### Writing Documentation

````markdown
# Good documentation example

## Feature: Two-Speaker Podcast Generation

### Overview

This feature generates natural-sounding conversations between two AI hosts discussing PDF content.

### Usage

```python
# Generate a two-speaker podcast
config = {
    'filename': 'document.pdf',
    'podcast': True,
    'two_speakers': True
}
result = generate_audio(config)
```
````

### Implementation Details

The feature uses Google's Gemini AI to create dialogue scripts, then converts them to speech using Edge-TTS.

### Configuration Options

- `voice_alex`: Voice for the analytical host (default: en-GB-LibbyNeural)
- `voice_jordan`: Voice for the enthusiastic host (default: en-US-AriaNeural)

```

## Release Process

### Version Numbering

We use Semantic Versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version numbers**
2. **Update CHANGELOG.md**
3. **Run full test suite**
4. **Update documentation**
5. **Create release notes**
6. **Tag the release**
7. **Deploy to production**

## Getting Help

### Resources

- **Documentation**: Check the docs directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join our community Discord server (if available)

### Mentorship

New contributors can request mentorship:

1. **Comment on beginner-friendly issues**
2. **Ask questions in discussions**
3. **Request code reviews**
4. **Join pair programming sessions**

## Recognition

We appreciate all contributions and recognize contributors through:

- **Contributors file**: Listed in CONTRIBUTORS.md
- **Release notes**: Mentioned in release announcements
- **Special badges**: For significant contributors
- **Featured contributions**: Highlighted in project updates

## License

By contributing to DocaCast, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to DocaCast! Your help makes this project better for everyone. 🎙️✨
```
