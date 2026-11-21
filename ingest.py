import os

import psycopg
from dotenv import load_dotenv

from arxiv_client import download_pdf
from chunker import Chunk, chunk_segments
from pdf_parser import extract_segments


def save_chunks(conn: psycopg.Connection, paper_id: int, chunks: list[Chunk]) -> None:
    # 先删掉这篇论文的旧文本块，再插入新的。事务由调用方负责
    conn.execute("DELETE FROM chunks WHERE paper_id = %s", (paper_id,))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO chunks (paper_id, chunk_index, section, page_start, page_end, content, token_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (paper_id, c.chunk_index, c.section, c.page_start, c.page_end, c.content, c.token_count)
                for c in chunks
            ],
        )


def ingest_paper(conn: psycopg.Connection, paper_id: int) -> int:
    arxiv_id, pdf_url = conn.execute(
        "SELECT arxiv_id, pdf_url FROM papers WHERE id = %s", (paper_id,)
    ).fetchone()
    try:
        # 慢操作（下载、解析、切块）放在事务外面
        pdf_path = download_pdf(arxiv_id, pdf_url)
        chunks = chunk_segments(extract_segments(pdf_path))
        if not chunks:
            raise ValueError("PDF 里没有提取到文字")
        # 只有"删 + 插"放在同一个事务里
        with conn.transaction():
            save_chunks(conn, paper_id, chunks)
        return len(chunks)
    except Exception as e:
        conn.execute("UPDATE papers SET ingest_status = 'failed' WHERE id = %s", (paper_id,))
        print(f"{arxiv_id} 处理失败：{e}")
        return 0


if __name__ == "__main__":
    load_dotenv()
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        rows = conn.execute(
            "SELECT id, arxiv_id FROM papers WHERE ingest_status = 'pending' ORDER BY id"
        ).fetchall()
        for paper_id, arxiv_id in rows:
            count = ingest_paper(conn, paper_id)
            print(f"{arxiv_id}：{count} 块")