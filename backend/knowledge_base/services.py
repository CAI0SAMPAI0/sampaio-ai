import os
import hashlib
import pypdf

class DeterministicEmbeddings:
    """
    Um gerador de embeddings determinístico para desenvolvimento local e testes.
    Mapeia strings para vetores de 384 dimensões usando hashing determinístico em Python puro.
    Evita dependência do numpy para maior portabilidade.
    """
    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        dim = 384
        vector = [0.0] * dim
        text_bytes = text.encode('utf-8', errors='ignore')
        
        for i in range(12):  # 12 hashes de 32 bytes = 384 floats
            h = hashlib.sha256(text_bytes + str(i).encode('utf-8')).digest()
            for j in range(32):
                val = (h[j] / 255.0) - 0.5
                vector[i * 32 + j] = val
                
        # Normaliza L2 em Python puro
        sq_sum = sum(x * x for x in vector)
        norm = sq_sum ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
            
        return vector


def cosine_similarity(a, b):
    """
    Calcula a similaridade de cosseno entre dois vetores de mesma dimensão.
    Como os vetores do DeterministicEmbeddings são normalizados L2, a similaridade de cosseno
    é simplesmente o produto escalar entre eles.
    """
    return sum(x * y for x, y in zip(a, b))


def split_text_recursively(text, chunk_size=800, chunk_overlap=150):
    """
    Divisor de texto recursivo em Python puro que simula o RecursiveCharacterTextSplitter.
    Divide o texto usando parágrafos, quebras de linha e espaços, garantindo que
    cada chunk fique dentro do limite chunk_size com a sobreposição chunk_overlap.
    """
    separators = ["\n\n", "\n", " ", ""]
    
    def _split(text_to_split, current_seps):
        if len(text_to_split) <= chunk_size:
            return [text_to_split]
            
        if not current_seps:
            return [text_to_split[i:i+chunk_size] for i in range(0, len(text_to_split), chunk_size)]
            
        sep = current_seps[0]
        parts = text_to_split.split(sep)
        
        current_chunks = []
        buffer = ""
        
        for part in parts:
            part_len = len(part)
            sep_len = len(sep) if buffer else 0
            
            if len(buffer) + part_len + sep_len > chunk_size:
                if buffer:
                    current_chunks.append(buffer)
                    # Keep overlap
                    overlap_start = max(0, len(buffer) - chunk_overlap)
                    buffer = buffer[overlap_start:]
                
                if part_len > chunk_size:
                    sub_chunks = _split(part, current_seps[1:])
                    for sc in sub_chunks[:-1]:
                        current_chunks.append(sc)
                    buffer = sub_chunks[-1]
                else:
                    buffer = part
            else:
                if buffer:
                    buffer += sep + part
                else:
                    buffer = part
                    
        if buffer:
            current_chunks.append(buffer)
            
        return current_chunks

    return _split(text, separators)


def extract_text_from_file(file_path, ext):
    """
    Extrai o texto de um arquivo com base na sua extensão.
    Retorna uma lista de tuplas: (número_da_página, texto_da_página)
    """
    text_by_page = []
    
    if ext == 'pdf':
        try:
            reader = pypdf.PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_by_page.append((idx + 1, page_text))
        except Exception as e:
            print(f"Erro ao extrair PDF: {e}")
    elif ext in ['txt', 'md', 'markdown', 'csv']:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                text_by_page.append((1, content))
        except Exception as e:
            print(f"Erro ao ler arquivo de texto: {e}")
    elif ext == 'docx':
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            
            with zipfile.ZipFile(file_path) as docx:
                xml_content = docx.read('word/document.xml')
                root = ET.fromstring(xml_content)
                paragraphs = []
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                for p in root.findall('.//w:p', ns):
                    texts = [r.text for r in p.findall('.//w:t', ns) if r.text]
                    if texts:
                        paragraphs.append(''.join(texts))
                text = '\n'.join(paragraphs)
                text_by_page.append((1, text))
        except Exception as e:
            print(f"Erro ao ler DOCX: {e}")
            text_by_page.append((1, f"[Erro ou DOCX sem texto legível: {os.path.basename(file_path)}]"))
    elif ext == 'epub':
        try:
            import zipfile
            import re
            
            html_tags_re = re.compile(r'<[^>]+>')
            
            with zipfile.ZipFile(file_path) as epub:
                # Find all files inside the epub zip that contain HTML/XHTML content
                content_files = [f for f in epub.namelist() if f.lower().endswith(('.xhtml', '.html', '.htm'))]
                # Sort them
                content_files.sort()
                
                text_parts = []
                for file_name in content_files:
                    try:
                        content = epub.read(file_name).decode('utf-8', errors='ignore')
                        # Remove HTML tags
                        cleaned_text = html_tags_re.sub(' ', content)
                        # Normalize spaces and HTML entities
                        cleaned_text = cleaned_text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'")
                        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                        if cleaned_text:
                            text_parts.append(cleaned_text)
                    except Exception as inner_e:
                        print(f"Erro ao ler arquivo {file_name} do EPUB: {inner_e}")
                
                full_text = '\n\n'.join(text_parts)
                if full_text:
                    text_by_page.append((1, full_text))
                else:
                    text_by_page.append((1, f"[EPUB sem texto legível: {os.path.basename(file_path)}]"))
        except Exception as e:
            print(f"Erro ao ler EPUB: {e}")
            text_by_page.append((1, f"[Erro ao ler EPUB {os.path.basename(file_path)}: {e}]"))
    else:
        text_by_page.append((1, f"[Conteúdo indexado do arquivo {ext.upper()}: {os.path.basename(file_path)}]"))
        
    return text_by_page


def process_document_into_chunks(document):
    """
    Processa um documento enviado: extrai texto, divide em chunks e salva no banco de dados.
    """
    from .models import KnowledgeChunk
    
    file_path = document.file.path
    ext = document.file_type.lower()
    
    # 1. Extração de texto
    pages = extract_text_from_file(file_path, ext)
    if not pages:
        document.processing_status = 'failed'
        document.save()
        return False
        
    embedder = DeterministicEmbeddings()
    chunks_to_create = []
    
    # 2. Divisão em chunks e geração de embeddings
    for page_num, page_text in pages:
        chunks = split_text_recursively(page_text, chunk_size=800, chunk_overlap=150)
        if not chunks:
            continue
            
        embeddings = embedder.embed_documents(chunks)
        
        for chunk_text, emb in zip(chunks, embeddings):
            chunks_to_create.append(
                KnowledgeChunk(
                    document=document,
                    content=chunk_text,
                    page_number=page_num,
                    embedding=emb
                )
            )
            
    # Salva no banco de dados
    if chunks_to_create:
        KnowledgeChunk.objects.bulk_create(chunks_to_create)
        document.chunks_count = len(chunks_to_create)
        document.processing_status = 'completed'
    else:
        document.processing_status = 'failed'
        
    document.save()
    return True


def search_similar_chunks(user, query_text, top_k=5):
    """
    Realiza a busca semântica calculando a similaridade de cosseno localmente
    entre o embedding da consulta e os chunks do usuário no banco de dados.
    Retorna uma lista de tuplas: (score, chunk)
    """
    from .models import KnowledgeChunk
    
    # 1. Gera embedding da busca
    embedder = DeterministicEmbeddings()
    query_vector = embedder.embed_query(query_text)
    
    # 2. Filtra os chunks pertencentes a documentos do usuário
    chunks = KnowledgeChunk.objects.filter(document__user=user)
    
    # 3. Calcula scores de similaridade de cosseno (produto escalar)
    scored_chunks = []
    for chunk in chunks:
        score = cosine_similarity(query_vector, chunk.embedding)
        scored_chunks.append((score, chunk))
        
    # 4. Ordena por score de forma decrescente
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    return scored_chunks[:top_k]
