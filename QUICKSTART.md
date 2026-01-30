# CaptionFoundry Quickstart Guide

This guide walks you through setting up CaptionFoundry with a vision AI backend for automatic image captioning.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Vision Backend Setup](#vision-backend-setup)
   - [Option A: Ollama (Recommended)](#option-a-ollama-recommended)
   - [Option B: LM Studio](#option-b-lm-studio)
3. [CaptionFoundry Installation](#captionfoundry-installation)
4. [First Run](#first-run)
5. [Captioning Your First Dataset](#captioning-your-first-dataset)
6. [Model Recommendations](#model-recommendations)
7. [Tips & Best Practices](#tips--best-practices)

---

## Prerequisites

Before installing CaptionFoundry, ensure you have:

- **Python 3.10 or higher** - [Download from python.org](https://python.org)
- **Node.js 18 or higher** - [Download from nodejs.org](https://nodejs.org)
- **8GB+ RAM** - Vision models need memory (16GB recommended for larger models)
- **GPU (optional)** - Speeds up captioning significantly; CPU works but is slower

---

## Vision Backend Setup

CaptionFoundry requires a local vision model server to generate captions. You have two options:

### Option A: Ollama (Recommended)

[Ollama](https://ollama.ai/) is the easiest way to run local AI models. It handles model downloading, GPU acceleration, and provides a simple API.

#### 1. Install Ollama

**Windows:**
Download and run the installer from [ollama.ai/download](https://ollama.ai/download)

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

#### 2. Start Ollama

Ollama should start automatically after installation. If not:

```bash
ollama serve
```

This starts the Ollama server on `http://localhost:11434`

#### 3. Pull a Vision Model

Open a terminal and pull a vision model. We recommend **Qwen3-VL** for best captioning quality:

**Small (4B parameters) - Fast, good quality:**
```bash
ollama pull qwen/qwen3-vl-4b
```

**Medium (8B parameters) - Better quality, slower:**
```bash
ollama pull qwen/qwen3-vl-8b
```

**Alternative models:**
```bash
# Qwen 2.5 VL (non-thinking, faster)
ollama pull qwen2.5-vl:7b

# LLaVA (good general purpose)
ollama pull llava:7b

# Moondream (very fast, smaller)
ollama pull moondream
```

#### 4. Verify Installation

Test that the model works:
```bash
ollama run qwen/qwen3-vl-4b "describe this image" --image path/to/any/image.jpg
```

You should see a description of the image.

---

### Option B: LM Studio

[LM Studio](https://lmstudio.ai/) provides a GUI for running local models with more control over parameters.

#### 1. Install LM Studio

Download from [lmstudio.ai](https://lmstudio.ai/) and install.

#### 2. Download a Vision Model

1. Open LM Studio
2. Go to the **Discover** tab
3. Search for a vision model (e.g., "qwen vl" or "llava")
4. Download your preferred model

#### 3. Start the Local Server

1. Go to the **Local Server** tab (left sidebar)
2. Load your vision model
3. Click **Start Server**
4. Note the server URL (default: `http://localhost:1234`)

#### 4. Configure CaptionFoundry

Update `config/settings.yaml`:
```yaml
vision:
  backend: lmstudio
  lmstudio_url: http://localhost:1234
```

---

## CaptionFoundry Installation

#### 1. Clone or Download

Download CaptionFoundry to your preferred location.

#### 2. Run the Installer

**Windows:**
```batch
install.bat
```

**Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

This creates a Python virtual environment and installs all dependencies.

#### 3. Configure Vision Backend

Edit `config/settings.yaml` to match your setup:

```yaml
vision:
  backend: ollama                    # "ollama" or "lmstudio"
  ollama_url: http://localhost:11434
  lmstudio_url: http://localhost:1234
  default_model: qwen/qwen3-vl-4b    # Your installed model
  max_tokens: 8192                   # Important for thinking models!
  timeout_seconds: 120
```

> **Important:** Qwen3-VL models use "thinking" tokens internally. Set `max_tokens` to 8192 or higher to ensure captions aren't cut off.

---

## First Run

#### 1. Start Your Vision Backend

Make sure Ollama or LM Studio is running with your vision model loaded.

**Ollama:**
```bash
ollama serve
```

**LM Studio:** Start the local server with your model loaded.

#### 2. Start CaptionFoundry

**Windows:**
```batch
start.bat
```

**Linux/macOS:**
```bash
./start.sh
```

The application window will open once the backend is ready.

#### 3. Verify Connection

In CaptionFoundry:
1. Click the **Settings** tab
2. Check the "Vision Backend" section
3. You should see your models listed in the dropdown

If no models appear, check that your backend is running.

---

## Captioning Your First Dataset

### Step 1: Add an Image Folder

- **Drag and drop** a folder containing images onto the Folders panel
- Or click **Add Folder** and select a folder

CaptionFoundry will scan the folder and generate thumbnails.

### Step 2: Create a Dataset

1. Click on your folder to view thumbnails
2. Select images (click to select, Ctrl+click for multiple, or "Select All")
3. Click **Create Dataset**
4. Give your dataset a name and description

### Step 3: Create a Caption Set

1. In the Datasets tab, click your dataset
2. Click **Add Caption Set**
3. Choose a style:
   - **Natural** - One-sentence descriptions (good for general training)
   - **Detailed** - 2-3 sentence comprehensive descriptions
   - **Tags** - Comma-separated booru-style tags (good for anime models)
   - **Custom** - Write your own vision model prompt (see below)
4. Optionally add a trigger phrase (e.g., "Nova Chorus, a woman") that will prefix all captions
5. Click Create

#### Using Custom Prompts

The **Custom** style lets you write your own prompt for the vision model. This gives you complete control over how captions are generated.

When you select Custom:
1. Click one of the template buttons (Copy Natural, Copy Detailed, Copy Tags) to start with a working prompt
2. Modify the prompt to fit your needs
3. The prompt should instruct the model to output JSON with `caption`, `quality`, and `flags` fields

Example use cases for custom prompts:
- Focus on specific attributes (e.g., "describe only the clothing")
- Use a specific vocabulary or style
- Include or exclude certain types of information
- Adjust the level of detail

### Step 4: Auto-Caption

1. Select your caption set from the dropdown
2. Click **Auto-Caption All**
3. Watch the progress as each image is captioned
4. Quality scores will appear on each thumbnail

### Step 5: Review and Edit

1. Click any image to open the caption editor
2. Review the generated caption and quality score
3. Edit as needed
4. Use arrow keys or navigation buttons to move between images
5. Changes save automatically

### Step 6: Export

1. Click **Export Dataset**
2. Choose:
   - **Caption Set** - Which caption set to export
   - **Image Format** - JPEG, PNG, or WebP
   - **Quality** - Compression quality (95 recommended)
   - **Destination** - Where to save the export
3. Click Export
4. Your dataset will be exported with sequential naming (000001.jpg, 000001.txt, etc.)

---

## Model Recommendations

### For Best Caption Quality

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `qwen/qwen3-vl-4b` | 4B | Fast | Very Good | General use, good balance |
| `qwen/qwen3-vl-8b` | 8B | Medium | Excellent | High quality captions |
| `qwen2.5-vl:7b` | 7B | Fast | Very Good | When you want speed |

### For Speed (Lower VRAM)

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `moondream` | 1.6B | Very Fast | Good | Quick captioning, low resources |
| `llava:7b` | 7B | Fast | Good | General purpose |

### VRAM Requirements (Approximate)

| Model Size | Minimum VRAM | Recommended |
|------------|--------------|-------------|
| 1-2B | 4GB | 6GB |
| 4B | 6GB | 8GB |
| 7-8B | 8GB | 12GB |

> **Tip:** If you're running out of VRAM, try a smaller model or use CPU mode (slower but works).

---

## Tips & Best Practices

### Captioning Quality

1. **Use appropriate caption styles**:
   - **Tags** - Best for anime/stylized images and models trained on booru data
   - **Natural** - Good for realistic photos and general-purpose models
   - **Detailed** - When you need comprehensive descriptions
   - **Custom** - When you need specific formatting or vocabulary

2. **Review the quality flags** - They help identify captions that may need manual attention:
   - 🔴 Red = Needs attention
   - 🟡 Yellow = Minor issues
   - 🟢 Green = Good

3. **Edit as needed** - AI captions are a starting point; human review improves quality

### Performance

1. **GPU acceleration** - Use a GPU if available; it's 5-10x faster than CPU

2. **Batch size** - Process one image at a time to avoid VRAM issues

3. **Model selection** - Start with a smaller model and upgrade if quality isn't sufficient

### Dataset Organization

1. **One concept per dataset** - Keep datasets focused (e.g., "character poses" vs "backgrounds")

2. **Consistent naming** - Use descriptive dataset names you'll recognize later

3. **Multiple caption sets** - Create different caption styles to compare results

### Export Tips

1. **Use JPEG for training** - Most training frameworks expect JPEG
2. **Quality 95** - Good balance of quality and file size
3. **Sequential naming** - Required by most training tools

---

## Troubleshooting

### "No vision models found"

1. Check that Ollama/LM Studio is running
2. Verify you've pulled/downloaded a vision model
3. Test with: `ollama list` (should show your model)

### Captions are cut off

Increase `max_tokens` in `config/settings.yaml`:
```yaml
vision:
  max_tokens: 8192  # or higher
```

### Slow captioning

1. Use a smaller model (try `moondream`)
2. Ensure GPU is being used (check Ollama output for "cuda" or "metal")
3. Close other GPU-intensive applications

### Out of memory

1. Use a smaller model
2. Restart Ollama: `ollama stop` then `ollama serve`
3. Close other applications using GPU memory

---

## Next Steps

- Read the full [README.md](README.md) for architecture details
- Explore the API at `http://localhost:8675/docs` when running
- Join discussions and report issues on GitHub

Happy captioning! 🎨
