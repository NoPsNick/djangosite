from django.core.cache import caches


def get_cached_data(manager, cache_key, serializer_class, timeout):
    file_cache = caches['file_based']
    cached_data = file_cache.get(cache_key)

    if cached_data is None:
        queryset = manager.order_by('modified', 'created')
        if queryset.exists():
            serializer = serializer_class(queryset, many=True)
            cached_data = serializer.data
            file_cache.set(cache_key, cached_data, timeout=timeout)

    return cached_data