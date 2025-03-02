from elasticsearch import AsyncElasticsearch

es_host = "http://elasticsearch:9200"


def get_es_instance():
    return AsyncElasticsearch(hosts=[es_host])
