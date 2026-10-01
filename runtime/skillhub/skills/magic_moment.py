"""Magic Moment driver — local reference implementation (ffmpeg).

The hosted "magic moment" feature (AI highlight detection) has no public API,
so this driver provides an honest local equivalent: cut shareable clips from
talking-head footage, burn in captions from an SRT file, and optionally
reframe to vertical 9:16 — all with a local ffmpeg install.

Requires: ffmpeg and ffprobe on PATH. No network, no credentials.
This is a local reimplementation, not the provider's hosted pipeline.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil

from ..driver import ActionDef
from ..errors import UpstreamError

SKILL = "magic-moment"
REQUIRED_ENV: list[str] = []
SETUP_HELP = "Install ffmpeg (https://ffmpeg.org/download.html) and make sure it is on PATH."


def _need_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise UpstreamError(SKILL, "ffmpeg not found on PATH. " + SETUP_HELP)
    return exe


def _need_ffprobe() -> str:
    exe = shutil.which("ffprobe")
    if not exe:
        raise UpstreamError(SKILL, "ffprobe not found on PATH. " + SETUP_HELP)
    return exe


async def _run(cmd: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode != 0:
        raise UpstreamError(SKILL, f"command failed: {' '.join(cmd[:2])} — {err.decode()[-500:]}")
    return out.decode()


def _escape_subtitles_path(path: str) -> str:
    # subtitles filter needs : ' \\ escaped inside the filter graph
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


async def probe(params: dict) -> dict:
    path = params["input_path"]
    if not os.path.exists(path):
        raise UpstreamError(SKILL, f"input file not found: {path}")
    raw = await _run([_need_ffprobe(), "-v", "quiet", "-print_format", "json",
                      "-show_format", "-show_streams", path])
    info = json.loads(raw)
    fmt = info.get("format", {})
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    return {"status": "ok", "duration_s": float(fmt.get("duration", 0) or 0),
            "size_bytes": int(fmt.get("size", 0) or 0),
            "width": video.get("width"), "height": video.get("height"),
            "fps": video.get("r_frame_rate"), "codec": video.get("codec_name")}


async def cut_clip(params: dict) -> dict:
    """Cut a clip, optionally burn SRT captions and reframe to vertical 9:16."""
    src = params["input_path"]
    if not os.path.exists(src):
        raise UpstreamError(SKILL, f"input file not found: {src}")
    out = params["output_path"]
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)

    vf: list[str] = []
    if params.get("vertical"):
        # center-crop to 9:16 for Shorts/Reels/TikTok
        vf.append("crop=ih*9/16:ih")
    srt = params.get("srt_path")
    if srt:
        if not os.path.exists(srt):
            raise UpstreamError(SKILL, f"SRT file not found: {srt}")
        vf.append(f"subtitles={_escape_subtitles_path(os.path.abspath(srt))}")
    scale = params.get("scale_width")
    if scale:
        vf.append(f"scale={int(scale)}:-2")

    cmd = [_need_ffmpeg(), "-y", "-v", "error",
           "-ss", str(params.get("start", 0))]
    if params.get("end") is not None:
        cmd += ["-to", str(params["end"])]
    elif params.get("duration") is not None:
        cmd += ["-t", str(params["duration"])]
    cmd += ["-i", src]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-movflags", "+faststart", out]
    await _run(cmd)
    size = os.path.getsize(out)
    return {"status": "ok", "output_path": os.path.abspath(out),
            "size_bytes": size,
            "note": "local ffmpeg cut; highlight selection was manual, not AI-detected"}


async def extract_thumbnail(params: dict) -> dict:
    src = params["input_path"]
    if not os.path.exists(src):
        raise UpstreamError(SKILL, f"input file not found: {src}")
    out = params["output_path"]
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    await _run([_need_ffmpeg(), "-y", "-v", "error",
                "-ss", str(params.get("at", 1)), "-i", src,
                "-frames:v", "1", "-q:v", "3", out])
    return {"status": "ok", "output_path": os.path.abspath(out)}


ACTIONS = {
    "probe": ActionDef(
        "Inspect a video file: duration, resolution, fps, codec.",
        {"input_path": {"type": "string"}}, ["input_path"], probe),
    "cut_clip": ActionDef(
        "Cut a shareable clip from footage (needs confirm=true). Optional SRT caption "
        "burn-in and vertical 9:16 reframe for Shorts/Reels/TikTok.",
        {"input_path": {"type": "string"},
         "output_path": {"type": "string"},
         "start": {"type": "string", "description": "Start time, seconds or HH:MM:SS", "default": "0"},
         "end": {"type": "string", "description": "End time (exclusive with duration)"},
         "duration": {"type": "string", "description": "Clip length in seconds (exclusive with end)"},
         "srt_path": {"type": "string", "description": "Optional SRT subtitle file to burn in"},
         "vertical": {"type": "boolean", "default": False,
                       "description": "Center-crop to 9:16 vertical"},
         "scale_width": {"type": "integer", "description": "Optional output width px (height auto)"}},
        ["input_path", "output_path"], cut_clip, write=True),
    "extract_thumbnail": ActionDef(
        "Grab a still thumbnail frame from a video (needs confirm=true).",
        {"input_path": {"type": "string"},
         "output_path": {"type": "string"},
         "at": {"type": "string", "description": "Timestamp, seconds or HH:MM:SS", "default": "1"}},
        ["input_path", "output_path"], extract_thumbnail, write=True),
}
