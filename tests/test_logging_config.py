import json
import logging

from logging_config import JsonFormatter, log_with_fields


def test_json_formatter_produz_json_valido_com_campos_extras():
    logger = logging.getLogger("velour.test")
    record = logger.makeRecord(
        "velour.test", logging.INFO, __file__, 1, "algo aconteceu", (), None,
    )
    record.extra_fields = {"user_id": 42, "path": "/appointments"}
    formatted = JsonFormatter().format(record)

    payload = json.loads(formatted)
    assert payload["message"] == "algo aconteceu"
    assert payload["level"] == "INFO"
    assert payload["user_id"] == 42
    assert payload["path"] == "/appointments"


def test_json_formatter_sem_campos_extras_nao_quebra():
    logger = logging.getLogger("velour.test2")
    record = logger.makeRecord(
        "velour.test2", logging.WARNING, __file__, 1, "sem extras", (), None,
    )
    formatted = JsonFormatter().format(record)
    payload = json.loads(formatted)
    assert payload["level"] == "WARNING"


def test_log_with_fields_anexa_extra_fields(caplog):
    logger = logging.getLogger("velour.test3")
    with caplog.at_level(logging.INFO, logger="velour.test3"):
        log_with_fields(logger, logging.INFO, "evento", chave="valor")
    assert len(caplog.records) == 1
    assert caplog.records[0].extra_fields == {"chave": "valor"}
