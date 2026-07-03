class NewsIngestionError(Exception):
    pass


class RetryableFetchError(NewsIngestionError):
    pass


class NonRetryableFetchError(NewsIngestionError):
    pass
