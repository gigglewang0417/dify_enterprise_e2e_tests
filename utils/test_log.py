from common.observability import attach_json, log_kv


def log_step_data(title, **data):
    log_kv(title, data)


def log_step_result(title, result):
    attach_json(title, result)


def log_resource_ids(**ids):
    if ids:
        log_kv("resource ids", ids)
