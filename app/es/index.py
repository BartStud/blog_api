from app.es.instance import get_es_instance
from app.models import Post


async def init_indices(es_client):
    await init_post_index(es_client)
    return True


async def create_index_if_not_exists(es_client, index_name, index_body):
    if not await es_client.indices.exists(index=index_name):
        await es_client.indices.create(index=index_name, body=index_body)


async def init_post_index(es_client):
    index_name = "posts"
    index_body = (
        {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "author_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "polish",
                        "fields": {"raw": {"type": "keyword"}},
                    },
                    "short_description": {
                        "type": "text",
                        "analyzer": "polish",
                        "fields": {"raw": {"type": "keyword"}},
                    },
                    "content": {"type": "text", "analyzer": "polish"},
                    "published": {"type": "boolean"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "published_at": {"type": "date"},
                    "keywords": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {"raw": {"type": "keyword"}},
                    },
                }
            },
        },
    )

    await create_index_if_not_exists(es_client, index_name, index_body)
    return True


async def es_index_post(post: Post):
    es_client = get_es_instance()
    await es_client.index(
        index="posts",
        id=post.id,
        body={
            "id": post.id,
            "author_id": post.author_id,
            "title": post.title,
            "short_description": post.short_description,
            "content": post.content,
            "published": post.published,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "published_at": post.published_at,
            "keywords": post.keywords,
        },
    )


async def es_delete_post(post_id: int):
    es_client = get_es_instance()
    try:
        await es_client.delete(index="posts", id=post_id)
    except Exception as e:
        print(f"Błąd podczas usuwania dokumentu: {e}")
