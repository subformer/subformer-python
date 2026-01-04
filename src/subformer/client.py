"""Subformer API client."""

import time
from typing import Any, Iterator, Optional, Union

import httpx

from subformer.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SubformerError,
    ValidationError,
)
from subformer.types import (
    DailyUsage,
    DubSource,
    Job,
    JobType,
    Language,
    PaginatedJobs,
    PresetVoice,
    RateLimit,
    TargetVoice,
    UploadedVoice,
    UploadUrl,
    Usage,
    User,
    Voice,
)


DEFAULT_BASE_URL = "https://api.subformer.com/v1"
DEFAULT_TIMEOUT = 30.0


class BaseClient:
    """Base client with shared functionality."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error responses from the API."""
        try:
            data = response.json()
            message = data.get("message", response.text)
            code = data.get("code")
        except Exception:
            message = response.text
            code = None

        if response.status_code == 401:
            raise AuthenticationError(message)
        elif response.status_code == 404:
            raise NotFoundError(message)
        elif response.status_code == 429:
            raise RateLimitError(message)
        elif response.status_code == 400:
            raise ValidationError(message, data=data.get("data") if "data" in locals() else None)
        else:
            raise SubformerError(message, status_code=response.status_code, code=code)


class Subformer(BaseClient):
    """Synchronous Subformer API client.

    Example:
        ```python
        from subformer import Subformer

        client = Subformer(api_key="sk_subformer_...")

        # Create a dubbing job
        job = client.dub(
            source="youtube",
            url="https://youtube.com/watch?v=VIDEO_ID",
            language="es-ES"
        )

        # Wait for completion
        job = client.wait_for_job(job.id)
        print(f"Done! Output: {job.output}")
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__(api_key, base_url, timeout)
        self._client = httpx.Client(timeout=timeout)

    def __enter__(self) -> "Subformer":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        response = self._client.request(
            method,
            url,
            headers=self._get_headers(),
            json=json,
            params=params,
        )

        if not response.is_success:
            self._handle_error(response)

        if response.status_code == 204:
            return None

        return response.json()

    # ==================== Dubbing ====================

    def dub(
        self,
        source: Union[DubSource, str],
        url: str,
        language: Union[Language, str],
        disable_watermark: bool = False,
    ) -> Job:
        """Create a video dubbing job.

        Args:
            source: Source type (youtube, tiktok, instagram, facebook, x, url)
            url: URL of the video to dub
            language: Target language for dubbing
            disable_watermark: Disable watermark (requires paid plan)

        Returns:
            The created job

        Example:
            ```python
            job = client.dub(
                source="youtube",
                url="https://youtube.com/watch?v=dQw4w9WgXcQ",
                language="es-ES"
            )
            ```
        """
        if isinstance(source, DubSource):
            source = source.value
        if isinstance(language, Language):
            language = language.value

        data = self._request(
            "POST",
            "/dub",
            json={
                "type": source,
                "url": url,
                "toLanguage": language,
                "disableWatermark": disable_watermark,
            },
        )
        return Job.model_validate(data["job"])

    def get_languages(self) -> list[str]:
        """Get list of supported languages for dubbing.

        Returns:
            List of language codes (e.g., ["en-US", "es-ES", ...])
        """
        return self._request("GET", "/metadata/dub/languages")

    # ==================== Jobs ====================

    def get_job(self, job_id: str) -> Job:
        """Get a job by ID.

        Args:
            job_id: The job ID

        Returns:
            The job
        """
        data = self._request("GET", f"/jobs/{job_id}")
        return Job.model_validate(data)

    def list_jobs(
        self,
        offset: int = 0,
        limit: int = 12,
        type: Optional[Union[JobType, str]] = None,
    ) -> PaginatedJobs:
        """List jobs for the authenticated user.

        Args:
            offset: Number of items to skip
            limit: Maximum number of items to return
            type: Filter by job type

        Returns:
            Paginated list of jobs
        """
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if type:
            params["type"] = type.value if isinstance(type, JobType) else type

        data = self._request("GET", "/jobs", params=params)
        return PaginatedJobs.model_validate(data)

    def delete_jobs(self, job_ids: list[str]) -> bool:
        """Delete jobs by IDs.

        Args:
            job_ids: List of job IDs to delete (max 50)

        Returns:
            True if successful
        """
        data = self._request("DELETE", "/jobs", json={"jobIds": job_ids})
        return data.get("success", False)

    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: Optional[float] = None,
    ) -> Job:
        """Wait for a job to complete.

        Args:
            job_id: The job ID
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait (None for no timeout)

        Returns:
            The completed job

        Raises:
            TimeoutError: If the job doesn't complete within the timeout
        """
        start_time = time.time()

        while True:
            job = self.get_job(job_id)
            if job.is_complete:
                return job

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

            time.sleep(poll_interval)

    # ==================== Voice Cloning ====================

    def clone_voice(
        self,
        source_audio_url: str,
        target_voice: TargetVoice,
    ) -> Job:
        """Create a voice cloning job.

        Args:
            source_audio_url: URL of the source audio to transform
            target_voice: Target voice (preset or uploaded)

        Returns:
            The created job
        """
        if isinstance(target_voice, PresetVoice):
            voice_data = {"mode": "preset", "presetVoiceId": target_voice.preset_voice_id}
        else:
            voice_data = {"mode": "upload", "targetAudioUrl": target_voice.target_audio_url}

        data = self._request(
            "POST",
            "/voice/clone",
            json={
                "sourceAudioUrl": source_audio_url,
                "targetVoice": voice_data,
            },
        )
        return Job.model_validate(data["job"])

    def synthesize_voice(
        self,
        text: str,
        target_voice: TargetVoice,
    ) -> Job:
        """Create a voice synthesis (text-to-speech) job.

        Args:
            text: Text to synthesize
            target_voice: Target voice (preset or uploaded)

        Returns:
            The created job
        """
        if isinstance(target_voice, PresetVoice):
            voice_data = {"mode": "preset", "presetVoiceId": target_voice.preset_voice_id}
        else:
            voice_data = {"mode": "upload", "targetAudioUrl": target_voice.target_audio_url}

        data = self._request(
            "POST",
            "/voice/synthesize",
            json={
                "text": text,
                "targetVoice": voice_data,
            },
        )
        return Job.model_validate(data["job"])

    # ==================== Voice Library ====================

    def list_voices(self) -> list[Voice]:
        """List all voices in the user's voice library.

        Returns:
            List of voices
        """
        data = self._request("GET", "/voices")
        return [Voice.model_validate(v) for v in data]

    def get_voice(self, voice_id: str) -> Voice:
        """Get a voice by ID.

        Args:
            voice_id: The voice ID

        Returns:
            The voice
        """
        data = self._request("GET", f"/voices/{voice_id}")
        return Voice.model_validate(data)

    def create_voice(
        self,
        name: str,
        audio_url: str,
        gender: str,
        duration: float,
    ) -> Voice:
        """Create a new voice in the voice library.

        Args:
            name: Voice name
            audio_url: URL of the voice audio sample
            gender: Voice gender ("male" or "female")
            duration: Duration of audio sample in milliseconds

        Returns:
            The created voice
        """
        data = self._request(
            "POST",
            "/voices",
            json={
                "name": name,
                "audioUrl": audio_url,
                "gender": gender,
                "duration": duration,
            },
        )
        return Voice.model_validate(data)

    def update_voice(
        self,
        voice_id: str,
        name: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> Voice:
        """Update a voice in the voice library.

        Args:
            voice_id: The voice ID
            name: New voice name
            gender: New voice gender

        Returns:
            The updated voice
        """
        payload: dict[str, Any] = {"voiceId": voice_id}
        if name is not None:
            payload["name"] = name
        if gender is not None:
            payload["gender"] = gender

        data = self._request("PUT", f"/voices/{voice_id}", json=payload)
        return Voice.model_validate(data)

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice from the voice library.

        Args:
            voice_id: The voice ID

        Returns:
            True if successful
        """
        data = self._request("DELETE", f"/voices/{voice_id}", json={"voiceId": voice_id})
        return data.get("success", False)

    def generate_voice_upload_url(
        self,
        file_name: str,
        content_type: str,
    ) -> UploadUrl:
        """Generate a presigned URL for uploading voice audio.

        Args:
            file_name: Name of the file to upload
            content_type: MIME type of the file (e.g., "audio/mp3")

        Returns:
            Upload URL details
        """
        data = self._request(
            "POST",
            "/voices/upload-url",
            json={
                "fileName": file_name,
                "contentType": content_type,
            },
        )
        return UploadUrl.model_validate(data)

    # ==================== Billing ====================

    def get_usage(self) -> Usage:
        """Get current billing period usage statistics.

        Returns:
            Current usage including credits, plan limits, and subscription details
        """
        data = self._request("GET", "/billing/usage")
        return Usage.model_validate(data)

    def get_usage_history(self) -> list[DailyUsage]:
        """Get daily usage statistics for the past 30 days.

        Returns:
            List of daily usage records grouped by task type
        """
        data = self._request("GET", "/billing/usage-history")
        return [DailyUsage.model_validate(d) for d in data]

    # ==================== Users ====================

    def get_me(self) -> User:
        """Get the currently authenticated user's profile.

        Returns:
            User profile information
        """
        data = self._request("GET", "/users/me")
        return User.model_validate(data)

    def update_me(
        self,
        name: str,
        email: str,
    ) -> User:
        """Update the currently authenticated user's profile.

        Args:
            name: New name
            email: New email

        Returns:
            Updated user profile
        """
        data = self._request(
            "PUT",
            "/users/me",
            json={
                "name": name,
                "email": email,
            },
        )
        return User.model_validate(data["user"])

    def get_rate_limit(self) -> RateLimit:
        """Get the current rate limit status for creating dubbing jobs.

        Returns:
            Rate limit status including remaining count and limit
        """
        data = self._request("GET", "/users/me/rate-limit")
        return RateLimit.model_validate(data)


class AsyncSubformer(BaseClient):
    """Asynchronous Subformer API client.

    Example:
        ```python
        import asyncio
        from subformer import AsyncSubformer

        async def main():
            async with AsyncSubformer(api_key="sk_subformer_...") as client:
                job = await client.dub(
                    source="youtube",
                    url="https://youtube.com/watch?v=VIDEO_ID",
                    language="es-ES"
                )
                job = await client.wait_for_job(job.id)
                print(f"Done! Output: {job.output}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__(api_key, base_url, timeout)
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "AsyncSubformer":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        response = await self._client.request(
            method,
            url,
            headers=self._get_headers(),
            json=json,
            params=params,
        )

        if not response.is_success:
            self._handle_error(response)

        if response.status_code == 204:
            return None

        return response.json()

    # ==================== Dubbing ====================

    async def dub(
        self,
        source: Union[DubSource, str],
        url: str,
        language: Union[Language, str],
        disable_watermark: bool = False,
    ) -> Job:
        """Create a video dubbing job."""
        if isinstance(source, DubSource):
            source = source.value
        if isinstance(language, Language):
            language = language.value

        data = await self._request(
            "POST",
            "/dub",
            json={
                "type": source,
                "url": url,
                "toLanguage": language,
                "disableWatermark": disable_watermark,
            },
        )
        return Job.model_validate(data["job"])

    async def get_languages(self) -> list[str]:
        """Get list of supported languages for dubbing."""
        return await self._request("GET", "/metadata/dub/languages")

    # ==================== Jobs ====================

    async def get_job(self, job_id: str) -> Job:
        """Get a job by ID."""
        data = await self._request("GET", f"/jobs/{job_id}")
        return Job.model_validate(data)

    async def list_jobs(
        self,
        offset: int = 0,
        limit: int = 12,
        type: Optional[Union[JobType, str]] = None,
    ) -> PaginatedJobs:
        """List jobs for the authenticated user."""
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if type:
            params["type"] = type.value if isinstance(type, JobType) else type

        data = await self._request("GET", "/jobs", params=params)
        return PaginatedJobs.model_validate(data)

    async def delete_jobs(self, job_ids: list[str]) -> bool:
        """Delete jobs by IDs."""
        data = await self._request("DELETE", "/jobs", json={"jobIds": job_ids})
        return data.get("success", False)

    async def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 2.0,
        timeout: Optional[float] = None,
    ) -> Job:
        """Wait for a job to complete."""
        import asyncio

        start_time = time.time()

        while True:
            job = await self.get_job(job_id)
            if job.is_complete:
                return job

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

            await asyncio.sleep(poll_interval)

    # ==================== Voice Cloning ====================

    async def clone_voice(
        self,
        source_audio_url: str,
        target_voice: TargetVoice,
    ) -> Job:
        """Create a voice cloning job."""
        if isinstance(target_voice, PresetVoice):
            voice_data = {"mode": "preset", "presetVoiceId": target_voice.preset_voice_id}
        else:
            voice_data = {"mode": "upload", "targetAudioUrl": target_voice.target_audio_url}

        data = await self._request(
            "POST",
            "/voice/clone",
            json={
                "sourceAudioUrl": source_audio_url,
                "targetVoice": voice_data,
            },
        )
        return Job.model_validate(data["job"])

    async def synthesize_voice(
        self,
        text: str,
        target_voice: TargetVoice,
    ) -> Job:
        """Create a voice synthesis (text-to-speech) job."""
        if isinstance(target_voice, PresetVoice):
            voice_data = {"mode": "preset", "presetVoiceId": target_voice.preset_voice_id}
        else:
            voice_data = {"mode": "upload", "targetAudioUrl": target_voice.target_audio_url}

        data = await self._request(
            "POST",
            "/voice/synthesize",
            json={
                "text": text,
                "targetVoice": voice_data,
            },
        )
        return Job.model_validate(data["job"])

    # ==================== Voice Library ====================

    async def list_voices(self) -> list[Voice]:
        """List all voices in the user's voice library."""
        data = await self._request("GET", "/voices")
        return [Voice.model_validate(v) for v in data]

    async def get_voice(self, voice_id: str) -> Voice:
        """Get a voice by ID."""
        data = await self._request("GET", f"/voices/{voice_id}")
        return Voice.model_validate(data)

    async def create_voice(
        self,
        name: str,
        audio_url: str,
        gender: str,
        duration: float,
    ) -> Voice:
        """Create a new voice in the voice library."""
        data = await self._request(
            "POST",
            "/voices",
            json={
                "name": name,
                "audioUrl": audio_url,
                "gender": gender,
                "duration": duration,
            },
        )
        return Voice.model_validate(data)

    async def update_voice(
        self,
        voice_id: str,
        name: Optional[str] = None,
        gender: Optional[str] = None,
    ) -> Voice:
        """Update a voice in the voice library."""
        payload: dict[str, Any] = {"voiceId": voice_id}
        if name is not None:
            payload["name"] = name
        if gender is not None:
            payload["gender"] = gender

        data = await self._request("PUT", f"/voices/{voice_id}", json=payload)
        return Voice.model_validate(data)

    async def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice from the voice library."""
        data = await self._request("DELETE", f"/voices/{voice_id}", json={"voiceId": voice_id})
        return data.get("success", False)

    async def generate_voice_upload_url(
        self,
        file_name: str,
        content_type: str,
    ) -> UploadUrl:
        """Generate a presigned URL for uploading voice audio."""
        data = await self._request(
            "POST",
            "/voices/upload-url",
            json={
                "fileName": file_name,
                "contentType": content_type,
            },
        )
        return UploadUrl.model_validate(data)

    # ==================== Billing ====================

    async def get_usage(self) -> Usage:
        """Get current billing period usage statistics."""
        data = await self._request("GET", "/billing/usage")
        return Usage.model_validate(data)

    async def get_usage_history(self) -> list[DailyUsage]:
        """Get daily usage statistics for the past 30 days."""
        data = await self._request("GET", "/billing/usage-history")
        return [DailyUsage.model_validate(d) for d in data]

    # ==================== Users ====================

    async def get_me(self) -> User:
        """Get the currently authenticated user's profile."""
        data = await self._request("GET", "/users/me")
        return User.model_validate(data)

    async def update_me(
        self,
        name: str,
        email: str,
    ) -> User:
        """Update the currently authenticated user's profile."""
        data = await self._request(
            "PUT",
            "/users/me",
            json={
                "name": name,
                "email": email,
            },
        )
        return User.model_validate(data["user"])

    async def get_rate_limit(self) -> RateLimit:
        """Get the current rate limit status for creating dubbing jobs."""
        data = await self._request("GET", "/users/me/rate-limit")
        return RateLimit.model_validate(data)
