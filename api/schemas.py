from pydantic import BaseModel
from typing import List, Optional


class ExtractRequest(BaseModel):
    file_id: str
    convert_to_wav: bool = False


class StemFile(BaseModel):
    name: str
    path: str  # relative path under the job output directory
    is_wav: bool


class ExtractResponse(BaseModel):
    job_id: str
    song_name: str
    stems: List[StemFile]
    error: Optional[str] = None
