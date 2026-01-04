# 🎬 Subformer Python SDK

[![PyPI version](https://badge.fury.io/py/subformer.svg)](https://pypi.org/project/subformer/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Official Python SDK for [Subformer](https://subformer.com)** — AI-powered video dubbing, voice cloning, and text-to-speech API.

🌍 Dub videos into 50+ languages | 🎙️ Clone any voice | 🔊 Generate natural speech

---

## ✨ Features

- 🎥 **Video Dubbing** — Automatically translate and dub YouTube, TikTok, Instagram, Facebook, X (Twitter), and any video URL
- 🗣️ **Voice Cloning** — Transform audio to match any target voice
- 📝 **Text-to-Speech** — Generate natural-sounding speech from text
- 🎵 **Voice Library** — Save and manage custom voices
- ⚡ **Async Support** — Full async/await support for high-performance applications
- 🔄 **Automatic Retries** — Built-in error handling and job polling

## 📦 Installation

```bash
pip install subformer
```

## 🚀 Quick Start

### Video Dubbing

Dub any video into 50+ languages with one API call:

```python
from subformer import Subformer

client = Subformer(api_key="sk_subformer_...")

# Dub a YouTube video to Spanish
job = client.dub(
    source="youtube",
    url="https://youtube.com/watch?v=VIDEO_ID",
    language="es-ES"
)

# Wait for completion
job = client.wait_for_job(job.id)

# Get the dubbed video URL
print(f"Dubbed video: {job.output['videoUrl']}")
```

### Voice Cloning

Clone any voice and apply it to audio:

```python
from subformer import Subformer, PresetVoice

client = Subformer(api_key="sk_subformer_...")

# Clone voice using a preset
job = client.clone_voice(
    source_audio_url="https://example.com/speech.mp3",
    target_voice=PresetVoice(preset_voice_id="morgan-freeman")
)

job = client.wait_for_job(job.id)
print(f"Cloned audio: {job.output['audioUrl']}")
```

### Text-to-Speech

Generate natural speech from text:

```python
from subformer import Subformer, UploadedVoice

client = Subformer(api_key="sk_subformer_...")

# Synthesize speech with a custom voice
job = client.synthesize_voice(
    text="Hello, welcome to Subformer!",
    target_voice=UploadedVoice(target_audio_url="https://example.com/my-voice.mp3")
)

job = client.wait_for_job(job.id)
print(f"Generated audio: {job.output['audioUrl']}")
```

## 🔄 Async Support

For high-performance applications, use the async client:

```python
import asyncio
from subformer import AsyncSubformer

async def main():
    async with AsyncSubformer(api_key="sk_subformer_...") as client:
        # Dub multiple videos concurrently
        jobs = await asyncio.gather(
            client.dub("youtube", "https://youtube.com/watch?v=VIDEO1", "es-ES"),
            client.dub("youtube", "https://youtube.com/watch?v=VIDEO2", "fr-FR"),
            client.dub("youtube", "https://youtube.com/watch?v=VIDEO3", "de-DE"),
        )

        # Wait for all to complete
        results = await asyncio.gather(
            *[client.wait_for_job(job.id) for job in jobs]
        )

        for result in results:
            print(f"Completed: {result.id}")

asyncio.run(main())
```

## 📚 API Reference

### Client Initialization

```python
from subformer import Subformer, AsyncSubformer

# Sync client
client = Subformer(
    api_key="sk_subformer_...",
    base_url="https://api.subformer.com/v1",  # optional
    timeout=30.0  # optional, in seconds
)

# Async client
async_client = AsyncSubformer(api_key="sk_subformer_...")
```

### Dubbing

| Method | Description |
|--------|-------------|
| `dub(source, url, language)` | Create a video dubbing job |
| `get_languages()` | Get list of supported languages |

**Supported Sources:** `youtube`, `tiktok`, `instagram`, `facebook`, `x`, `url`

### Jobs

| Method | Description |
|--------|-------------|
| `get_job(job_id)` | Get job by ID |
| `list_jobs(offset, limit, type)` | List all jobs |
| `delete_jobs(job_ids)` | Delete jobs |
| `wait_for_job(job_id, poll_interval, timeout)` | Wait for job completion |

### Voice Cloning & Synthesis

| Method | Description |
|--------|-------------|
| `clone_voice(source_audio_url, target_voice)` | Clone a voice |
| `synthesize_voice(text, target_voice)` | Text-to-speech |

### Voice Library

| Method | Description |
|--------|-------------|
| `list_voices()` | List saved voices |
| `get_voice(voice_id)` | Get voice by ID |
| `create_voice(name, audio_url, gender, duration)` | Create a voice |
| `update_voice(voice_id, name, gender)` | Update a voice |
| `delete_voice(voice_id)` | Delete a voice |

## 🌍 Supported Languages

Subformer supports 70+ languages for video dubbing:

| Language | Code | Language | Code |
|----------|------|----------|------|
| Afrikaans | `af-ZA` | Albanian | `sq-AL` |
| Arabic | `ar-SA` | Armenian | `hy-AM` |
| Azerbaijani | `az-AZ` | Belarusian | `be-BY` |
| Bengali | `bn-IN` | Bosnian | `bs-BA` |
| Bulgarian | `bg-BG` | Burmese | `my-MM` |
| Catalan | `ca-ES` | Chinese (Simplified) | `zh-CN` |
| Chinese (Traditional) | `zh-TW` | Croatian | `hr-HR` |
| Czech | `cs-CZ` | Danish | `da-DK` |
| Dutch | `nl-NL` | English | `en-US` |
| Estonian | `et-EE` | Filipino | `fil-PH` |
| Finnish | `fi-FI` | French | `fr-FR` |
| Galician | `gl-ES` | Georgian | `ka-GE` |
| German | `de-DE` | Greek | `el-GR` |
| Gujarati | `gu-IN` | Hebrew | `he-IL` |
| Hindi | `hi-IN` | Hungarian | `hu-HU` |
| Icelandic | `is-IS` | Indonesian | `id-ID` |
| Italian | `it-IT` | Japanese | `ja-JP` |
| Javanese | `jv-ID` | Kannada | `kn-IN` |
| Kazakh | `kk-KZ` | Khmer | `km-KH` |
| Korean | `ko-KR` | Latin | `la-VA` |
| Latvian | `lv-LV` | Lithuanian | `lt-LT` |
| Macedonian | `mk-MK` | Malay | `ms-MY` |
| Malayalam | `ml-IN` | Maltese | `mt-MT` |
| Marathi | `mr-IN` | Mongolian | `mn-MN` |
| Norwegian | `no-NO` | Persian | `fa-IR` |
| Polish | `pl-PL` | Portuguese (Brazil) | `pt-BR` |
| Punjabi | `pa-IN` | Romanian | `ro-RO` |
| Russian | `ru-RU` | Serbian | `sr-RS` |
| Slovak | `sk-SK` | Slovenian | `sl-SI` |
| Spanish | `es-ES` | Swahili | `sw-KE` |
| Swedish | `sv-SE` | Tagalog | `tl-PH` |
| Tamil | `ta-IN` | Telugu | `te-IN` |
| Thai | `th-TH` | Turkish | `tr-TR` |
| Ukrainian | `uk-UA` | Urdu | `ur-PK` |
| Uzbek | `uz-UZ` | Vietnamese | `vi-VN` |
| Welsh | `cy-GB` | | |

## ⚠️ Error Handling

```python
from subformer import Subformer, SubformerError, AuthenticationError, RateLimitError

client = Subformer(api_key="sk_subformer_...")

try:
    job = client.dub("youtube", "https://youtube.com/watch?v=VIDEO_ID", "es-ES")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Too many requests, please slow down")
except SubformerError as e:
    print(f"API error: {e.message} (code: {e.code})")
```

## 🔑 Getting Your API Key

1. Sign up at [subformer.com](https://subformer.com)
2. Go to [API Keys](https://subformer.com/dashboard/api-keys)
3. Create a new API key

## 📖 Documentation

- [API Documentation](https://subformer.com/docs/api)
- [Interactive API Reference](https://api.subformer.com/v1/docs)
- [OpenAPI Spec](https://api.subformer.com/v1/openapi.json)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by <a href="https://subformer.com">Subformer</a>
</p>
