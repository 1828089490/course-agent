import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

# 有编号的标题："1 Introduction"、"2.1 Notations and Definitions"、附录 "A FLARE Implementation Details"
# 编号最多两位数，避免把参考文献里的年份（如 "2019 Conference ..."）当成标题
HEADING_RE = re.compile(r"^(\d{1,2}(\.\d{1,2})*|[A-Z](\.\d{1,2})*)\s+[A-Z][^.]{2,80}$")
# 没有编号、但也是章节的标题
UNNUMBERED_HEADINGS = {"Abstract", "References", "Acknowledgments", "Acknowledgements", "Limitations"}


@dataclass
class Segment:
    section: str | None
    page: int
    text: str


def extract_pages(pdf_path: Path) -> list[str]:
    # 返回每一页的文字；列表下标 0 对应第 1 页
    reader = PdfReader(pdf_path)
    return [page.extract_text() or "" for page in reader.pages]


def is_heading(line: str) -> bool:
    if line in UNNUMBERED_HEADINGS:
        return True
    return HEADING_RE.match(line) is not None


def join_lines(lines: list[str]) -> str:
    text = ""
    for line in lines:
        if text.endswith("-"):
            text = text[:-1] + line  # 行尾断字：去掉连字符，和下一行直接拼接
        elif text:
            text += " " + line
        else:
            text = line
    return text


def extract_segments(pdf_path: Path) -> list[Segment]:
    segments = []
    section = None
    for page_number, page_text in enumerate(extract_pages(pdf_path), start=1):
        lines = []
        for raw_line in page_text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            if is_heading(line):
                # 遇到新标题：先把之前攒下的文字存成一个片段，再切换章节
                if lines:
                    segments.append(Segment(section, page_number, join_lines(lines)))
                    lines = []
                section = line
            else:
                lines.append(line)
        # 一页结束：把这一页剩下的文字存成一个片段
        if lines:
            segments.append(Segment(section, page_number, join_lines(lines)))
    return segments


if __name__ == "__main__":
    segments = extract_segments(Path("data/pdfs/2305.06983.pdf"))
    print("片段数：", len(segments))
    for s in segments:
        print(f"p{s.page:<3} {str(s.section)[:40]:<42} {len(s.text):>5} 字符  {s.text[:60]}")