from typing import List, Optional

convert_to_wav: bool = True
soundfont_path: str = "/path/to/your/soundfont.sf2"
output_path: Optional[str] = None  # None = place stems next to the source .mid file

midi_file_paths: List[str] = [
    "/path/to/your/file.mid",
    # "/path/to/another/file.mid",
]
