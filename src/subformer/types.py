"""Type definitions for Subformer SDK."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class JobState(str, Enum):
    """Job execution state."""

    QUEUED = "queued"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Type of background job."""

    VIDEO_DUBBING = "video-dubbing"
    VOICE_CLONING = "voice-cloning"
    VOICE_SYNTHESIS = "voice-synthesis"
    DUB_STUDIO_RENDER = "dub-studio-render-video"


class DubSource(str, Enum):
    """Source type for dubbing jobs."""

    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    X = "x"
    URL = "url"


class Language(str, Enum):
    """Supported languages for dubbing."""

    AFRIKAANS = "af-ZA"
    ARABIC = "ar-SA"
    AZERBAIJANI = "az-AZ"
    BELARUSIAN = "be-BY"
    BULGARIAN = "bg-BG"
    BENGALI = "bn-IN"
    BOSNIAN = "bs-BA"
    CATALAN = "ca-ES"
    CZECH = "cs-CZ"
    WELSH = "cy-GB"
    DANISH = "da-DK"
    GERMAN = "de-DE"
    GREEK = "el-GR"
    ENGLISH = "en-US"
    SPANISH = "es-ES"
    ESTONIAN = "et-EE"
    PERSIAN = "fa-IR"
    FINNISH = "fi-FI"
    FILIPINO = "fil-PH"
    FRENCH = "fr-FR"
    GALICIAN = "gl-ES"
    GUJARATI = "gu-IN"
    HEBREW = "he-IL"
    HINDI = "hi-IN"
    CROATIAN = "hr-HR"
    HUNGARIAN = "hu-HU"
    ARMENIAN = "hy-AM"
    INDONESIAN = "id-ID"
    ICELANDIC = "is-IS"
    ITALIAN = "it-IT"
    JAPANESE = "ja-JP"
    JAVANESE = "jv-ID"
    GEORGIAN = "ka-GE"
    KAZAKH = "kk-KZ"
    KHMER = "km-KH"
    KANNADA = "kn-IN"
    KOREAN = "ko-KR"
    LATIN = "la-VA"
    LITHUANIAN = "lt-LT"
    LATVIAN = "lv-LV"
    MACEDONIAN = "mk-MK"
    MALAYALAM = "ml-IN"
    MONGOLIAN = "mn-MN"
    MARATHI = "mr-IN"
    MALAY = "ms-MY"
    MALTESE = "mt-MT"
    BURMESE = "my-MM"
    DUTCH = "nl-NL"
    NORWEGIAN = "no-NO"
    PUNJABI = "pa-IN"
    POLISH = "pl-PL"
    PORTUGUESE = "pt-BR"
    ROMANIAN = "ro-RO"
    RUSSIAN = "ru-RU"
    SLOVAK = "sk-SK"
    SLOVENIAN = "sl-SI"
    ALBANIAN = "sq-AL"
    SERBIAN = "sr-RS"
    SWEDISH = "sv-SE"
    SWAHILI = "sw-KE"
    TAMIL = "ta-IN"
    TELUGU = "te-IN"
    THAI = "th-TH"
    TAGALOG = "tl-PH"
    TURKISH = "tr-TR"
    UKRAINIAN = "uk-UA"
    URDU = "ur-PK"
    UZBEK = "uz-UZ"
    VIETNAMESE = "vi-VN"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"


class JobProgress(BaseModel):
    """Progress information for a job."""

    progress: float = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Current status message")
    step: Optional[str] = Field(None, description="Current processing step")


class JobMetadata(BaseModel):
    """Metadata for a job."""

    title: Optional[str] = None
    thumbnail_url: Optional[str] = Field(None, alias="thumbnailUrl")
    duration: Optional[float] = None
    source_url: Optional[str] = Field(None, alias="sourceUrl")
    source_type: Optional[str] = Field(None, alias="sourceType")
    original_language: Optional[str] = Field(None, alias="originalLanguage")

    class Config:
        populate_by_name = True


class Job(BaseModel):
    """A background job."""

    id: str
    type: JobType
    user_id: str = Field(..., alias="userId")
    state: JobState
    input: Optional[Any] = None
    output: Optional[Any] = None
    metadata: Optional[JobMetadata] = None
    created_at: datetime = Field(..., alias="createdAt")
    progress: Optional[JobProgress] = None
    processed_on: Optional[datetime] = Field(None, alias="processedOn")
    finished_on: Optional[datetime] = Field(None, alias="finishedOn")
    credit_used: Optional[float] = Field(None, alias="creditUsed")

    class Config:
        populate_by_name = True

    @property
    def is_complete(self) -> bool:
        """Check if the job has completed (successfully or not)."""
        return self.state in (JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED)

    @property
    def is_successful(self) -> bool:
        """Check if the job completed successfully."""
        return self.state == JobState.COMPLETED


class Voice(BaseModel):
    """A saved voice in the voice library."""

    id: str
    name: str
    audio_url: str = Field(..., alias="audioUrl")
    gender: Literal["male", "female"]
    duration: float
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True


class PresetVoice(BaseModel):
    """Target voice using a preset."""

    mode: Literal["preset"] = "preset"
    preset_voice_id: str = Field(..., alias="presetVoiceId")

    class Config:
        populate_by_name = True


class UploadedVoice(BaseModel):
    """Target voice using an uploaded audio file."""

    mode: Literal["upload"] = "upload"
    target_audio_url: str = Field(..., alias="targetAudioUrl")

    class Config:
        populate_by_name = True


TargetVoice = Union[PresetVoice, UploadedVoice]


class PaginatedJobs(BaseModel):
    """Paginated list of jobs."""

    data: list[Job]
    total: int


class UsageData(BaseModel):
    """Billing usage data for active subscription."""

    used_credits: float = Field(..., alias="usedCredits")
    plan_credits: float = Field(..., alias="planCredits")
    total_events: int = Field(..., alias="totalEvents")
    current_plan: str = Field(..., alias="currentPlan")
    period_start: datetime = Field(..., alias="periodStart")
    period_end: datetime = Field(..., alias="periodEnd")

    class Config:
        populate_by_name = True


class Usage(BaseModel):
    """Current billing usage."""

    type: str
    data: UsageData


class DailyUsage(BaseModel):
    """Daily usage statistics."""

    date: str
    video_dubbing: int = Field(0, alias="video-dubbing")
    voice_cloning: int = Field(0, alias="voice-cloning")
    voice_synthesis: int = Field(0, alias="voice-synthesis")
    dub_studio_render: int = Field(0, alias="dub-studio-render-video")

    class Config:
        populate_by_name = True


class User(BaseModel):
    """User profile information."""

    id: str
    name: Optional[str] = None
    email: str
    email_verified: bool = Field(..., alias="emailVerified")
    image: Optional[str] = None
    preferred_target_language: Optional[str] = Field(None, alias="preferredTargetLanguage")

    class Config:
        populate_by_name = True


class RateLimit(BaseModel):
    """Rate limit status."""

    remaining: int
    limit: int
    reset: int
    bucket: str


class UploadUrl(BaseModel):
    """Presigned upload URL response."""

    upload_url: str = Field(..., alias="uploadUrl")
    file_url: str = Field(..., alias="fileUrl")
    key: str

    class Config:
        populate_by_name = True
