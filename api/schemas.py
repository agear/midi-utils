from pydantic import BaseModel
from typing import List, Optional


class ExtractRequest(BaseModel):
    file_id: str
    convert_to_wav: bool = False
    soundfont_id: Optional[str] = None  # None → use the bundled default


class StemFile(BaseModel):
    name: str
    path: str  # relative path under the job output directory
    is_wav: bool
    duration_seconds: Optional[float] = None


class ExtractResponse(BaseModel):
    job_id: str
    song_name: str
    stems: List[StemFile]
    error: Optional[str] = None
