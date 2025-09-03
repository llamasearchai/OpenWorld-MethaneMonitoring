"""Tests for logging utilities."""

import io
import json
import logging
from unittest.mock import patch

from openworld_methane.core.logging import (
    JSONFormatter,
    LogConfig,
    get_logger,
    log_error_with_context,
    log_with_context,
    setup_logging,
)


class TestLogConfig:
    def test_default_config(self):
        config = LogConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.output == "stderr"

    def test_custom_config(self):
        config = LogConfig(level="DEBUG", format="text", output="stdout")
        assert config.level == "DEBUG"
        assert config.format == "text"
        assert config.output == "stdout"


class TestJSONFormatter:
    def test_basic_formatting(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert parsed["message"] == "test message"
        assert "timestamp" in parsed

    def test_with_extra_data(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"user_id": "123", "action": "login"}

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["user_id"] == "123"
        assert parsed["action"] == "login"

    def test_with_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="error occurred",
                args=(),
                exc_info=sys.exc_info(),  # Use actual exc_info tuple
            )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "ValueError: test error" in parsed["exception"]


class TestSetupLogging:
    def test_default_setup(self):
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            setup_logging()

            mock_logger.setLevel.assert_called_with(logging.INFO)
            assert mock_logger.addHandler.called

    def test_debug_level(self):
        config = LogConfig(level="DEBUG")
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            setup_logging(config)

            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_text_format(self):
        config = LogConfig(format="text")
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = mock_get_logger.return_value
            setup_logging(config)

            # Should have added a handler
            assert mock_logger.addHandler.called

    def test_file_output(self):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            config = LogConfig(output=tmp.name)
            logger = setup_logging(config)

            # Test that we can log to the file
            test_logger = get_logger("test")
            test_logger.info("test message")

            # Clean up handlers to release file
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)


class TestGetLogger:
    def test_get_logger(self):
        logger = get_logger("test_module")
        assert logger.name == "openworld_methane.test_module"
        assert isinstance(logger, logging.Logger)

    def test_logger_hierarchy(self):
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name != logger2.name
        assert logger1.name.startswith("openworld_methane.")
        assert logger2.name.startswith("openworld_methane.")


class TestLogWithContext:
    def test_log_with_context(self):
        # Create a test handler to capture output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        logger = logging.getLogger("test")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        log_with_context(
            logger,
            logging.INFO,
            "test message",
            user_id="123",
            action="test"
        )

        output = stream.getvalue()
        parsed = json.loads(output)

        assert parsed["message"] == "test message"
        assert parsed["user_id"] == "123"
        assert parsed["action"] == "test"

    def test_log_error_with_context(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        logger = logging.getLogger("test")
        logger.setLevel(logging.ERROR)
        logger.addHandler(handler)

        try:
            raise ValueError("test error")
        except ValueError as e:
            log_error_with_context(
                logger,
                "An error occurred",
                exception=e,
                operation="test_operation"
            )

        output = stream.getvalue()
        parsed = json.loads(output)

        assert parsed["message"] == "An error occurred"
        assert parsed["operation"] == "test_operation"
        assert "exception" in parsed

    def test_log_error_without_exception(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JSONFormatter())

        logger = logging.getLogger("test")
        logger.setLevel(logging.ERROR)
        logger.addHandler(handler)

        log_error_with_context(
            logger,
            "An error occurred",
            operation="test_operation"
        )

        output = stream.getvalue()
        parsed = json.loads(output)

        assert parsed["message"] == "An error occurred"
        assert parsed["operation"] == "test_operation"
        assert "exception" not in parsed
