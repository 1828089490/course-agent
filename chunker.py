import math
import re
from dataclasses import dataclass
from pathlib import Path

import tiktoken

from pdf_parser import Segment, extract_segments

MAX_TOKENS = 500
# text-embedding-3-small 使用的分词方式，按它来数词元
ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass
class Sentence:
    section: str | None
    page: int
    text: str
    tokens: int


@dataclass
class Chunk:
    chunk_index: int
    section: str | None
    page_start: int
    page_end: int
    content: str
    token_count: int


def count_tokens(text: str) -> int:
    return len(ENCODING.encode(text))


def split_sentences(text: str) -> list[str]:
    # 在 . ? ! 后面、空格之后紧跟大写字母的地方切开
    # 只认大写字母，避免把 "et al. 2020"、"Fig. 3" 这类地方当成句子结尾
    return re.split(r"(?<=[.?!])\s+(?=[A-Z])", text)


def split_by_tokens(text: str) -> list[str]:
    # 兜底：一句话本身就超过上限（比如没有句号的表格文字），只能按词元数硬切
    tokens = ENCODING.encode(text)
    return [ENCODING.decode(tokens[i : i + MAX_TOKENS]) for i in range(0, len(tokens), MAX_TOKENS)]


def to_sentences(segments: list[Segment]) -> list[Sentence]:
    sentences = []
    for segment in segments:
        for text in split_sentences(segment.text):
            tokens = count_tokens(text)
            pieces = [text] if tokens <= MAX_TOKENS else split_by_tokens(text)
            for piece in pieces:
                sentences.append(Sentence(segment.section, segment.page, piece, count_tokens(piece)))
    return sentences


def build_chunk(chunk_index: int, sentences: list[Sentence]) -> Chunk:
    content = " ".join(s.text for s in sentences)
    return Chunk(
        chunk_index=chunk_index,
        section=sentences[0].section,
        page_start=sentences[0].page,
        page_end=sentences[-1].page,
        content=content,
        token_count=count_tokens(content),
    )


def group_by_section(sentences: list[Sentence]) -> list[list[Sentence]]:
    # 把相邻、属于同一章节的句子分到一组
    groups = []
    for sentence in sentences:
        if groups and groups[-1][0].section == sentence.section:
            groups[-1].append(sentence)
        else:
            groups.append([sentence])
    return groups


def target_size(remaining_tokens: int) -> float:
    # 剩下的内容至少要切成几块，平均每块多大
    return remaining_tokens / math.ceil(remaining_tokens / MAX_TOKENS)


def pack_section(sentences: list[Sentence]) -> list[list[Sentence]]:
    # 均匀切分：每块装到"平均大小"就封箱，避免最后剩下一个很小的尾巴
    packs = []
    current = []
    current_tokens = 0
    remaining = sum(s.tokens for s in sentences)
    target = target_size(remaining)
    for sentence in sentences:
        if current and (current_tokens >= target or current_tokens + sentence.tokens > MAX_TOKENS):
            packs.append(current)
            remaining -= current_tokens
            target = target_size(remaining)
            current, current_tokens = [], 0
        current.append(sentence)
        current_tokens += sentence.tokens
    if current:
        packs.append(current)
    return packs


def chunk_segments(segments: list[Segment]) -> list[Chunk]:
    chunks = []
    for group in group_by_section(to_sentences(segments)):
        for pack in pack_section(group):
            chunks.append(build_chunk(len(chunks), pack))
    return chunks


if __name__ == "__main__":
    chunks = chunk_segments(extract_segments(Path("data/pdfs/2305.06983.pdf")))
    print("块数：", len(chunks))
    for c in chunks:
        pages = f"{c.page_start}" if c.page_start == c.page_end else f"{c.page_start}-{c.page_end}"
        print(f"#{c.chunk_index:<3} p{pages:<6} {str(c.section)[:36]:<38} {c.token_count:>4} 词元  {c.content[:50]}")