# Just for accessing the config values/file
from app.config import settings
# print(f"GROQ API key: {settings.groq_api_key}")

import argparse
import hashlib
from pathlib import Path
import fitz
from app.knowledge import ensure_index,embed,clients

def chunks(text,size=1100,overlap=180):
    text = ' '.join(text.split())
    step = size-overlap
    return [text[i:i+size] for i in range(0,len(text),step) if len(text[i:i+size]) > 80]

def check_index():
    index = ensure_index()

    print("Index client:", type(index))
    print("Has documents API:", hasattr(index, "documents"))
    print("Has upsert API:", hasattr(index, "upsert"))


def check_index_schema():
    _, pc = clients()

    info = pc.indexes.describe(settings.pinecone_index)

    print("Index name:", settings.pinecone_index)
    print("Index schema:")
    print(info.schema)

def upsert_batch(index, batch):
    if not batch:
        return

    documents = [
        {
            "_id": item[0],
            "title": item[2]["file"],
            "chunk_text": item[1],
        }
        for item in batch
    ]

    index.documents.upsert(
        namespace="default",
        documents=documents,
    )

    print(f"Uploaded {len(documents)} documents", flush=True)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', default='data/medical_book.pdf')
    args = parser.parse_args()

    pdf = Path(args.pdf)

    if not pdf.exists():
        raise SystemExit(f'PDF not found: {pdf}')

    index = ensure_index()

    with fitz.open(pdf) as doc:
        batch = []

        for page_number, page in enumerate(doc, start=1):
            for part, content in enumerate(
                chunks(page.get_text()), start=1
            ):
                key = hashlib.sha256(
                    f'{pdf.name}:{page_number}:{part}:{content}'.encode()
                ).hexdigest()

                metadata = {
                    'page': page_number,
                    'text': content,
                    'file': pdf.name,
                }

                batch.append((key, content, metadata))

                if len(batch) >= 50:
                    upsert_batch(index, batch)
                    batch = []

            if page_number % 50 == 0:
                print(
                    f'Indexed pages: {page_number}/{len(doc)}',
                    flush=True
                )

        if batch:
            upsert_batch(index, batch)

    print('Ingestion complete')


if __name__ == '__main__':
    main()
    # check_index_schema()
# if __name__ == '__main__': main()
#if __name__ == '__main__': check_index()







