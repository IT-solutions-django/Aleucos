import logging
import json
import requests


class ElasticLogHandler(logging.Handler):
    def __init__(self, host, index):
        super().__init__()
        self.host = host.rstrip('/')
        self.index = index

    def emit(self, record):
        try:
            log_entry = self.format(record)
            url = f'{self.host}/{self.index}/_doc/'
            headers = {'Content-Type': 'application/json'}
            requests.post(url, data=log_entry, headers=headers, timeout=1)
        except Exception as e:
            print(f"Ошибка отправки лога в Elasticsearch: {e}")
