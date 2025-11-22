# 📖 Usage Examples

This guide provides practical examples of how to use DocaCast for various scenarios.

## Basic Usage Examples

### Example 1: Research Paper to Podcast

Convert an academic research paper into an engaging two-speaker podcast.

#### Step 1: Upload the Document

```bash
curl -X POST "http://127.0.0.1:8001/upload" \
  -F "file=@machine_learning_paper.pdf"
```

#### Step 2: Generate Podcast

```bash
curl -X POST "http://127.0.0.1:8001/generate-audio" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "machine_learning_paper.pdf",
    "podcast": true,
    "two_speakers": true,
    "content_style": "academic"
  }'
```

**Expected Output:**

- 15-20 minute conversation between Alex and Jordan
- Discussion of methodology, findings, and implications
- Natural interruptions and clarifying questions

### Example 2: Business Report Summary

Create a quick audio summary of a quarterly business report.

```javascript
const response = await fetch("http://127.0.0.1:8001/generate-audio", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    filename: "q4_business_report.pdf",
    podcast: false,
    two_speakers: false,
    content_style: "professional",
    max_duration: 10, // 10 minutes
  }),
});
```

### Example 3: Educational Content

Transform educational material into an engaging learning podcast.

```python
import requests

# Generate educational podcast
response = requests.post(
    'http://127.0.0.1:8001/generate-audio',
    json={
        'filename': 'biology_textbook_chapter.pdf',
        'podcast': True,
        'two_speakers': True,
        'content_style': 'educational',
        'voice_alex': 'en-GB-LibbyNeural',
        'voice_jordan': 'en-US-AriaNeural'
    }
)

audio_data = response.json()
print(f"Generated {audio_data['duration']} seconds of audio")
```

## Advanced Usage Scenarios

### Scenario 1: Multi-Document Analysis

Process multiple related documents and create a comprehensive discussion.

```python
import requests
import time

documents = [
    'climate_report_2023.pdf',
    'climate_report_2024.pdf',
    'climate_policy_analysis.pdf'
]

# Upload all documents
for doc in documents:
    with open(doc, 'rb') as f:
        requests.post('http://127.0.0.1:8001/upload', files={'file': f})

# Generate comparative analysis podcast
response = requests.post(
    'http://127.0.0.1:8001/generate-full-podcast',
    json={
        'filenames': documents,
        'analysis_type': 'comparative',
        'max_duration': 45
    }
)
```

### Scenario 2: Interactive Q&A Session

Use semantic search to create targeted discussions on specific topics.

```javascript
// First, search for specific content
const searchResponse = await fetch("http://127.0.0.1:8001/search", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "artificial intelligence ethics",
    filename: "ai_ethics_paper.pdf",
    top_k: 10,
  }),
});

const searchResults = await searchResponse.json();

// Generate focused discussion on search results
const audioResponse = await fetch("http://127.0.0.1:8001/generate-audio", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    filename: "ai_ethics_paper.pdf",
    podcast: true,
    two_speakers: true,
    focus_content: searchResults.results.map((r) => r.text),
    discussion_style: "debate",
  }),
});
```

### Scenario 3: Custom Voice Configuration

Use specific voices for different types of content.

```python
# Configuration for medical content
medical_config = {
    'filename': 'medical_research.pdf',
    'podcast': True,
    'two_speakers': True,
    'tts_engine': 'edge-tts',
    'voice_alex': 'en-GB-SoniaNeural',  # Professional female
    'voice_jordan': 'en-US-GuyNeural',   # Authoritative male
    'speaking_rate': 0.9,  # Slightly slower for medical terms
    'content_style': 'medical'
}

# Configuration for technology content
tech_config = {
    'filename': 'tech_innovation.pdf',
    'podcast': True,
    'two_speakers': True,
    'tts_engine': 'edge-tts',
    'voice_alex': 'en-GB-LibbyNeural',   # Curious female
    'voice_jordan': 'en-US-AriaNeural',  # Enthusiastic male
    'speaking_rate': 1.1,  # Faster for tech content
    'content_style': 'casual'
}
```

## Frontend Integration Examples

### React Component Integration

```tsx
import React, { useState } from "react";

function PodcastGenerator() {
  const [file, setFile] = useState<File | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!file) return;

    setIsGenerating(true);

    // Upload file
    const formData = new FormData();
    formData.append("file", file);

    await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    // Generate podcast
    const response = await fetch("/generate-audio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: file.name,
        podcast: true,
        two_speakers: true,
      }),
    });

    const result = await response.json();
    setAudioUrl(result.audio_url);
    setIsGenerating(false);
  };

  return (
    <div>
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button onClick={handleGenerate} disabled={!file || isGenerating}>
        {isGenerating ? "Generating..." : "Create Podcast"}
      </button>

      {audioUrl && (
        <audio controls src={audioUrl}>
          Your browser does not support audio playback.
        </audio>
      )}
    </div>
  );
}
```

### Vue.js Integration

```vue
<template>
  <div class="podcast-generator">
    <input type="file" @change="handleFileSelect" accept=".pdf" />
    <button @click="generatePodcast" :disabled="!selectedFile || isLoading">
      {{ isLoading ? "Generating..." : "Generate Podcast" }}
    </button>

    <div v-if="podcastData" class="podcast-player">
      <audio :src="podcastData.audio_url" controls></audio>
      <div class="chapters">
        <div
          v-for="chapter in podcastData.chapters"
          :key="chapter.index"
          class="chapter"
        >
          <strong>{{ chapter.speaker }}:</strong> {{ chapter.text }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedFile: null,
      isLoading: false,
      podcastData: null,
    };
  },
  methods: {
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
    },

    async generatePodcast() {
      this.isLoading = true;

      try {
        // Upload and generate
        const formData = new FormData();
        formData.append("file", this.selectedFile);

        await fetch("/upload", {
          method: "POST",
          body: formData,
        });

        const response = await fetch("/generate-audio", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: this.selectedFile.name,
            podcast: true,
            two_speakers: true,
          }),
        });

        this.podcastData = await response.json();
      } catch (error) {
        console.error("Error generating podcast:", error);
      } finally {
        this.isLoading = false;
      }
    },
  },
};
</script>
```

## Use Case Examples

### Use Case 1: Academic Research Review

**Scenario:** Convert multiple research papers into podcast discussions for literature review.

```python
def create_literature_review_podcast(paper_files):
    """Create a podcast reviewing multiple academic papers."""

    # Upload all papers
    for paper in paper_files:
        upload_file(paper)

    # Get summaries for each paper
    summaries = []
    for paper in paper_files:
        summary = get_document_summary(paper, summary_type='academic')
        summaries.append(summary)

    # Generate comparative discussion
    podcast_config = {
        'filenames': paper_files,
        'podcast': True,
        'two_speakers': True,
        'content_style': 'academic_review',
        'include_comparisons': True,
        'max_duration': 60  # 1 hour
    }

    return generate_podcast(podcast_config)

# Example usage
papers = [
    'deep_learning_2023.pdf',
    'neural_networks_advances.pdf',
    'ai_applications_healthcare.pdf'
]

podcast = create_literature_review_podcast(papers)
```

### Use Case 2: Business Meeting Preparation

**Scenario:** Create audio summaries of reports for busy executives.

```javascript
class BusinessReportProcessor {
  constructor(apiBaseUrl) {
    this.apiUrl = apiBaseUrl;
  }

  async createExecutiveBriefing(reportFile, urgencyLevel = "normal") {
    const config = {
      filename: reportFile,
      podcast: false, // Single narrator for efficiency
      two_speakers: false,
      content_style: "executive_summary",
      max_duration: urgencyLevel === "urgent" ? 5 : 10,
      include_action_items: true,
      include_key_metrics: true,
    };

    const response = await fetch(`${this.apiUrl}/generate-audio`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });

    return await response.json();
  }
}

// Usage
const processor = new BusinessReportProcessor("http://127.0.0.1:8001");
const briefing = await processor.createExecutiveBriefing(
  "quarterly_financial_report.pdf",
  "urgent"
);
```

### Use Case 3: Educational Content Creation

**Scenario:** Transform textbook chapters into engaging audio lessons.

```python
class EducationalPodcastCreator:
    def __init__(self, api_base_url):
        self.api_url = api_base_url

    def create_lesson_podcast(self, textbook_chapter, grade_level, subject):
        """Create age-appropriate educational podcast."""

        # Age-appropriate voice selection
        voice_config = self._get_voice_config(grade_level)

        config = {
            'filename': textbook_chapter,
            'podcast': True,
            'two_speakers': True,
            'content_style': 'educational',
            'grade_level': grade_level,
            'subject': subject,
            'include_examples': True,
            'include_quiz_questions': True,
            **voice_config
        }

        return self._generate_educational_content(config)

    def _get_voice_config(self, grade_level):
        if grade_level <= 5:  # Elementary
            return {
                'voice_alex': 'en-US-JennyNeural',  # Warm, friendly
                'voice_jordan': 'en-US-GuyNeural',   # Encouraging
                'speaking_rate': 0.9
            }
        elif grade_level <= 8:  # Middle school
            return {
                'voice_alex': 'en-GB-LibbyNeural',
                'voice_jordan': 'en-US-AriaNeural',
                'speaking_rate': 1.0
            }
        else:  # High school+
            return {
                'voice_alex': 'en-GB-SoniaNeural',
                'voice_jordan': 'en-US-DavisNeural',
                'speaking_rate': 1.1
            }

# Example usage
creator = EducationalPodcastCreator('http://127.0.0.1:8001')
biology_lesson = creator.create_lesson_podcast(
    'biology_chapter_photosynthesis.pdf',
    grade_level=9,
    subject='biology'
)
```

## Batch Processing Examples

### Process Multiple Documents

```bash
#!/bin/bash
# Batch process multiple PDFs

API_URL="http://127.0.0.1:8001"
INPUT_DIR="./documents"
OUTPUT_DIR="./generated_podcasts"

for pdf in "$INPUT_DIR"/*.pdf; do
    filename=$(basename "$pdf")
    echo "Processing $filename..."

    # Upload file
    curl -X POST "$API_URL/upload" -F "file=@$pdf"

    # Generate podcast
    curl -X POST "$API_URL/generate-audio" \
      -H "Content-Type: application/json" \
      -d "{
        \"filename\": \"$filename\",
        \"podcast\": true,
        \"two_speakers\": true
      }" \
      -o "$OUTPUT_DIR/${filename%.*}_podcast.json"

    echo "Completed $filename"
done
```

### Python Batch Processing

```python
import os
import requests
import json
from pathlib import Path

def batch_process_documents(input_dir, output_dir, config=None):
    """Batch process all PDFs in a directory."""

    default_config = {
        'podcast': True,
        'two_speakers': True,
        'content_style': 'conversational'
    }

    config = {**default_config, **(config or {})}

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for pdf_file in input_path.glob('*.pdf'):
        print(f"Processing {pdf_file.name}...")

        try:
            # Upload file
            with open(pdf_file, 'rb') as f:
                upload_response = requests.post(
                    'http://127.0.0.1:8001/upload',
                    files={'file': f}
                )
            upload_response.raise_for_status()

            # Generate podcast
            generation_config = {**config, 'filename': pdf_file.name}
            audio_response = requests.post(
                'http://127.0.0.1:8001/generate-audio',
                json=generation_config
            )
            audio_response.raise_for_status()

            # Save metadata
            result = audio_response.json()
            metadata_file = output_path / f"{pdf_file.stem}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"✓ Completed {pdf_file.name}")

        except Exception as e:
            print(f"✗ Failed to process {pdf_file.name}: {e}")

# Usage
batch_process_documents(
    input_dir='./research_papers',
    output_dir='./generated_podcasts',
    config={'content_style': 'academic', 'max_duration': 30}
)
```

## Error Handling Examples

### Robust Error Handling

```python
import requests
import time
from typing import Optional

class DocaCastClient:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')

    def generate_podcast_with_retry(
        self,
        filename: str,
        max_retries: int = 3,
        backoff_factor: float = 1.5
    ) -> Optional[dict]:
        """Generate podcast with retry logic and error handling."""

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f'{self.api_url}/generate-audio',
                    json={
                        'filename': filename,
                        'podcast': True,
                        'two_speakers': True
                    },
                    timeout=300  # 5 minute timeout
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = backoff_factor ** attempt
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 422:  # Invalid file
                    print(f"Invalid file format: {filename}")
                    return None
                else:
                    response.raise_for_status()

            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(backoff_factor ** attempt)
                    continue
                else:
                    print("Max retries exceeded")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(backoff_factor ** attempt)
                    continue
                else:
                    return None

        return None

# Usage
client = DocaCastClient('http://127.0.0.1:8001')
result = client.generate_podcast_with_retry('research_paper.pdf')

if result:
    print(f"Generated podcast: {result['audio_url']}")
else:
    print("Failed to generate podcast")
```

## Performance Optimization Examples

### Async Processing

```python
import asyncio
import aiohttp
import aiofiles

async def async_generate_podcast(session, filename, config):
    """Async podcast generation."""

    async with session.post(
        'http://127.0.0.1:8001/generate-audio',
        json={'filename': filename, **config}
    ) as response:
        return await response.json()

async def process_multiple_documents(documents, config):
    """Process multiple documents concurrently."""

    async with aiohttp.ClientSession() as session:
        tasks = [
            async_generate_podcast(session, doc, config)
            for doc in documents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            result for result in results
            if not isinstance(result, Exception)
        ]

# Usage
documents = ['doc1.pdf', 'doc2.pdf', 'doc3.pdf']
config = {'podcast': True, 'two_speakers': True}

results = asyncio.run(process_multiple_documents(documents, config))
print(f"Generated {len(results)} podcasts")
```

These examples demonstrate the flexibility and power of DocaCast for various use cases. Whether you're creating educational content, business summaries, or research discussions, DocaCast provides the tools to transform your documents into engaging audio experiences.
