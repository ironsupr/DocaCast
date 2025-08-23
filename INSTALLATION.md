# 🔧 Installation Guide

This guide provides detailed installation instructions for DocaCast on different operating systems.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for dependencies and models

### Recommended Requirements
- **RAM**: 16GB for better performance with large PDFs
- **CPU**: Multi-core processor for faster audio generation
- **GPU**: Optional, for accelerated AI processing

## Prerequisites

### 1. Python Installation

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```powershell
   python --version
   pip --version
   ```

#### macOS
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2. Node.js Installation

#### Windows
1. Download from [nodejs.org](https://nodejs.org/)
2. Run the installer
3. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

#### macOS
```bash
# Using Homebrew
brew install node

# Or using nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
```

#### Linux
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or using snap
sudo snap install node --classic
```

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/ironsupr/DocaCast.git
cd DocaCast
```

### 2. Backend Setup

#### Create Virtual Environment (Recommended)
```bash
# Windows
cd backend
python -m venv venv
venv\Scripts\activate

# macOS/Linux
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Verify Backend Installation
```bash
python -c "import fastapi, fitz, sentence_transformers; print('Backend dependencies installed successfully!')"
```

### 3. Frontend Setup

```bash
cd frontend/pdf-reader-ui
npm install
```

#### Verify Frontend Installation
```bash
npm run build
```

### 4. Environment Configuration

#### Backend Environment
Create `.env` file in `backend/` directory:
```env
GOOGLE_API_KEY=your_google_api_key_here
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8001
```

#### Frontend Environment
Create `.env` file in `frontend/pdf-reader-ui/` directory:
```env
VITE_ADOBE_CLIENT_ID=your_adobe_embed_client_id
VITE_API_BASE_URL=http://127.0.0.1:8001
```

## API Keys Setup

### Google API Key (Required)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Generative AI API
4. Create credentials (API Key)
5. Add the key to your backend `.env` file

### Adobe PDF Embed API (Required)
1. Visit [Adobe Developer Console](https://developer.adobe.com/)
2. Create a new project
3. Add PDF Embed API
4. Get your Client ID
5. Add to frontend `.env` file

## Troubleshooting

### Common Issues

#### Python Module Not Found
```bash
# Ensure virtual environment is activated
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

#### Node.js Permission Issues (Linux/macOS)
```bash
# Fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.profile
source ~/.profile
```

#### PyTorch/FAISS Installation Issues
```bash
# For CPU-only installation
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# For CUDA support (if you have NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Memory Issues with Large PDFs
- Increase system virtual memory
- Close other applications
- Process PDFs in smaller chunks

### Platform-Specific Issues

#### Windows
- Use PowerShell instead of Command Prompt
- Install Microsoft Visual C++ Build Tools if needed
- Ensure Windows Defender doesn't block downloads

#### macOS
- Install Xcode Command Line Tools: `xcode-select --install`
- Use Homebrew for package management
- Check system permissions for file access

#### Linux
- Install system dependencies:
  ```bash
  sudo apt-get install build-essential python3-dev portaudio19-dev
  ```
- Ensure sufficient file descriptors: `ulimit -n 4096`

## Verification

### Test Backend
```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8001
```
Visit: `http://127.0.0.1:8001/docs`

### Test Frontend
```bash
cd frontend/pdf-reader-ui
npm run dev
```
Visit: `http://localhost:5173`

## Performance Optimization

### Backend Optimization
- Use SSD storage for faster file I/O
- Increase Python memory limits for large PDFs
- Consider using GPU acceleration for embeddings

### Frontend Optimization
- Enable browser hardware acceleration
- Use modern browsers (Chrome, Firefox, Safari)
- Ensure stable internet connection for Adobe PDF API

## Next Steps

After successful installation:
1. Read the [API Documentation](API.md)
2. Check out [Usage Examples](EXAMPLES.md)
3. Review [Configuration Options](CONFIGURATION.md)

## Getting Help

If you encounter issues:
1. Check this troubleshooting section
2. Search existing GitHub issues
3. Create a new issue with detailed error information
4. Include system information and error logs
