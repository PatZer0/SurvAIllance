from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from logger import logger
from config import ChromaDBConfig, LLMConfig

PERSIST_DIR = ChromaDBConfig.persist_dir
QUERY_MODEL = LLMConfig.query_model
EMBED_MODEL = LLMConfig.embedding_model

vector_store = Chroma(
    collection_name='video_events',
    embedding_function=OllamaEmbeddings(model=QUERY_MODEL),
    persist_directory=PERSIST_DIR,
)

logger.info(f'成功加载向量数据库 {PERSIST_DIR}')

def vdb_add_event(text, metadata):
    """
    添加事件到数据库, 时间为索引
    """
    vector_store.add_texts(text, metadata)
    logger.info(f'成功向数据库添加事件')

def vdb_search_event(query):
    """
    搜索事件
    """
    results = vector_store.similarity_search(query=query, k=1)
    if results:
        logger.info(f'搜索结果: {results[0].page_content} [{results[0].metadata}]')
    else:
        logger.info(f'搜索结果为空')
