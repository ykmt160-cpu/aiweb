#!/usr/bin/env python3
"""works 폴더를 읽어서 works.js(작품 목록)를 만드는 스크립트.

사용법
  1) works/1반 ~ works/5반 폴더에 학생 html 파일을 넣는다.
       works/1반/홍길동.html
       works/1반/홍길동.png     <- (선택) 같은 이름의 이미지가 있으면 썸네일로 사용
  2) 이 폴더에서  python update.py  실행
  3) index.html, works.js, works 폴더를 통째로 웹에 올린다.

폴더 이름은 '1반', '1', '1-반', 'class1' 모두 인식합니다.
works 폴더 안에 '1반_홍길동.html' 처럼 파일명 앞에 반을 붙여도 인식합니다.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKS = ROOT / "works"
OUT = ROOT / "works.js"

HTML_EXT = {".html", ".htm"}
IMG_EXT = [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]
CLASS_RE = re.compile(r"(?:class[\s_-]*)?([1-5])\s*(?:반|-?\s*반)?", re.I)


def find_class(path: Path):
    """폴더명 또는 파일명에서 반 번호(1~5)를 찾는다."""
    rel = path.relative_to(WORKS)
    # 1) 폴더명 우선 (가까운 폴더부터)
    for part in reversed(rel.parts[:-1]):
        c = class_of(part)
        if c:
            return c
    # 2) 파일명 (예: 1반_홍길동, 3-김철수, 홍길동_3반)
    stem = unicodedata.normalize("NFC", path.stem)
    c = class_of(stem)
    if c:
        return c
    m = re.match(r"\s*0?([1-5])\s*[_\-\s]+", stem)
    if m:
        return int(m.group(1))
    return None


def class_of(text: str):
    """'1반', '01반', '3학년 2반', '2', 'class2', '3-2' 같은 이름에서 반 번호(1~5)를 찾는다."""
    text = unicodedata.normalize("NFC", text)
    m = re.search(r"(\d+)\s*반", text)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 5 else None
    m = re.fullmatch(r"\s*(?:class[\s_-]*)?0?([1-5])\s*", text, re.I)
    if m:
        return int(m.group(1))
    m = re.fullmatch(r"\s*\d+\s*[-_]\s*0?([1-5])\s*", text)
    if m:
        return int(m.group(1))
    return None


def display_name(path: Path):
    """파일명에서 학생 이름(작품명)을 만든다. 앞의 '1반_' 접두어는 제거."""
    name = unicodedata.normalize("NFC", path.stem)
    name = re.sub(r"^\s*0?[1-5]\s*(?:반)?\s*[_\-\s]+", "", name)
    name = name.replace("_", " ").strip()
    return name or path.stem


def find_thumb(html: Path):
    for ext in IMG_EXT:
        for cand in (html.with_suffix(ext), html.with_suffix(ext.upper())):
            if cand.exists():
                return cand
    return None


def posix(p: Path):
    return p.relative_to(ROOT).as_posix()


def main():
    if not WORKS.is_dir():
        WORKS.mkdir()
        for c in range(1, 6):
            (WORKS / f"{c}반").mkdir(exist_ok=True)
        print("works 폴더를 만들었어요. 1반~5반 폴더에 html을 넣고 다시 실행하세요.")

    items, skipped = [], []
    for f in sorted(WORKS.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in HTML_EXT:
            continue
        cls = find_class(f)
        if cls is None:
            skipped.append(posix(f))
            continue
        th = find_thumb(f)
        items.append({
            "cls": cls,
            "name": display_name(f),
            "file": posix(f),
            "thumb": posix(th) if th else "",
        })

    items.sort(key=lambda w: (w["cls"], w["name"]))
    OUT.write_text(
        "// update.py 가 자동으로 만든 파일입니다. 직접 수정하지 마세요.\n"
        "window.WORKS = " + json.dumps(items, ensure_ascii=False, indent=1) + ";\n",
        encoding="utf-8",
    )

    print(f"작품 {len(items)}개를 works.js 에 기록했어요.")
    for c in range(1, 6):
        n = sum(1 for w in items if w["cls"] == c)
        print(f"  {c}반: {n}개")
    no_thumb = sum(1 for w in items if not w["thumb"])
    if no_thumb:
        print(f"* 썸네일 이미지가 없는 작품 {no_thumb}개는 페이지 미리보기가 대신 표시됩니다.")
    if skipped:
        print("! 반을 알 수 없어 제외된 파일:")
        for s in skipped:
            print("   ", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
