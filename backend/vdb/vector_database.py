from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import hashlib

from logger import logger
from config import ChromaDBConfig, LLMConfig, RAGConfig

PERSIST_DIR = ChromaDBConfig.persist_dir
QUERY_MODEL = LLMConfig.query_model
EMBED_MODEL = LLMConfig.embedding_model

TOP_K = RAGConfig.top_k

vector_store = Chroma(
    collection_name='video_events',
    embedding_function=OllamaEmbeddings(model=EMBED_MODEL),
    persist_directory=PERSIST_DIR,
)

logger.info(f'成功加载向量数据库 {PERSIST_DIR}')


def generate_event_id(text, metadata):
    """
    根据事件描述和元数据生成唯一的事件ID。
    """
    unique_str = text + metadata.get('video_name', '') + metadata.get('start_time', '') + metadata.get('end_time', '')
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()


def vdb_add_events(texts, metadatas):
    """
    批量添加事件到数据库, 避免重复添加。
    """
    # 生成事件ID列表
    ids = [generate_event_id(text, meta) for text, meta in zip(texts, metadatas)]

    # 检查哪些事件已存在
    existing_ids = []
    for event_id in ids:
        existing = vector_store.get(ids=[event_id])
        if existing and len(existing['documents']) > 0:
            existing_ids.append(event_id)

    # 过滤掉已存在的事件
    new_texts = []
    new_metadatas = []
    new_ids = []
    for text, meta, event_id in zip(texts, metadatas, ids):
        if event_id not in existing_ids:
            new_texts.append(text)
            new_metadatas.append(meta)
            new_ids.append(event_id)
        else:
            logger.debug(f"事件已存在，跳过添加: {event_id}")

    # 添加新的事件
    if new_texts:
        vector_store.add_texts(new_texts, new_metadatas, ids=new_ids)
        logger.debug(f'成功向数据库添加 {len(new_texts)} 个新事件')
    else:
        logger.debug("没有新的事件需要添加")


def vdb_search_event(query):
    """
    搜索事件
    """
    results = vector_store.similarity_search(query=query, k=TOP_K)
    if results:
        for result in results:
            logger.debug(f'搜索结果: {result.page_content} [{result.metadata}]')
    else:
        logger.info(f'搜索结果为空')
    return results
