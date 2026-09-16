"""Cut the client's originals into what the site serves.

    python _tools/cut_images.py              # everything in _tools/image-picks.json
    python _tools/cut_images.py --images     # photographs only
    python _tools/cut_images.py --video      # the hero loop only
    python _tools/cut_images.py --og         # the share image only

Originals live in _originals/ (git-ignored; this repo is public). The picks
file names each original, the output name, an optional crop box
[left, top, right, bottom] in source pixels, and the alt text the page table
uses. Output: assets/img/<name>-1600.webp and <name>-800.webp, never
upscaled; assets/video/hero.webm, hero.mp4 and hero-poster.webp;
assets/og.jpg at 1200x630.

Output names are chosen by hand in the picks file; nothing here derives them
from the originals' file names.
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ORIGINALS = os.path.join(ROOT, "_originals")
IMG = os.path.join(ROOT, "assets", "img")
VIDEO = os.path.join(ROOT, "assets", "video")
PICKS = os.path.join(HERE, "image-picks.json")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", os.path.splitext(name)[0].lower()).strip("-")


def open_image(src):
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)          # phone photos carry rotation in EXIF
    return im.convert("RGB")


def checked_crop(im, crop):
    left, top, right, bottom = crop
    if not (0 <= left < right <= im.width and 0 <= top < bottom <= im.height):
        raise ValueError("crop %r is outside the %dx%d source" % (crop, im.width, im.height))
    return im.crop((left, top, right, bottom))


def cut_image(src, out_dir, name, crop=None, widths=(1600, 800)):
    im = open_image(src)
    if crop:
        im = checked_crop(im, crop)
    os.makedirs(out_dir, exist_ok=True)
    out = []
    for w in widths:
        frame = im
        if im.width > w:
            frame = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        path = os.path.join(out_dir, "%s-%d.webp" % (name, w))
        frame.save(path, "WEBP", quality=82, method=6)
        out.append(path)
    return out


def cut_og(src, out_path, crop=None):
    im = open_image(src)
    if crop:
        im = checked_crop(im, crop)
    im = ImageOps.fit(im, (1200, 630), Image.LANCZOS, centering=(0.5, 0.5))
    im.save(out_path, "JPEG", quality=84, optimize=True, progressive=True)
    return out_path


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def cut_video(src, out_dir, name, start, seconds, width=1280):
    os.makedirs(out_dir, exist_ok=True)
    common = [ffmpeg(), "-y", "-ss", str(start), "-t", str(seconds), "-i", src,
              "-vf", "scale=%d:-2,fps=24" % width, "-an"]
    webm = os.path.join(out_dir, name + ".webm")
    mp4 = os.path.join(out_dir, name + ".mp4")
    poster_png = os.path.join(out_dir, name + "-poster.png")
    subprocess.run(common + ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "36", "-row-mt", "1", webm], check=True)
    subprocess.run(common + ["-c:v", "libx264", "-crf", "27", "-preset", "slow", "-pix_fmt", "yuv420p",
                             "-movflags", "+faststart", mp4], check=True)
    subprocess.run([ffmpeg(), "-y", "-ss", str(start), "-i", src, "-frames:v", "1",
                    "-vf", "scale=%d:-2" % width, poster_png], check=True)
    poster = os.path.join(out_dir, name + "-poster.webp")
    Image.open(poster_png).convert("RGB").save(poster, "WEBP", quality=80, method=6)
    os.remove(poster_png)
    return [webm, mp4, poster]


def run(picks_path=PICKS, images=True, video=True, og=True):
    with open(picks_path, encoding="utf-8") as f:
        picks = json.load(f)
    if images:
        for p in picks.get("images", []):
            src = os.path.join(ORIGINALS, p["src"])
            for path in cut_image(src, IMG, p["name"], p.get("crop")):
                print("wrote", os.path.relpath(path, ROOT), os.path.getsize(path) // 1024, "KB")
    if video and picks.get("video"):
        v = picks["video"]
        for path in cut_video(os.path.join(ORIGINALS, v["src"]), VIDEO, v["name"], v["start"], v["seconds"]):
            print("wrote", os.path.relpath(path, ROOT), os.path.getsize(path) // 1024, "KB")
    if og and picks.get("og"):
        o = picks["og"]
        path = cut_og(os.path.join(ORIGINALS, o["src"]), os.path.join(ROOT, "assets", "og.jpg"), o.get("crop"))
        print("wrote", os.path.relpath(path, ROOT), os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if a.startswith("--")]
    run(images=not only or "--images" in only,
        video=not only or "--video" in only,
        og=not only or "--og" in only)
