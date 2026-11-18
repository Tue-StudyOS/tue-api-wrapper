from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from tue_api_wrapper.command import COMMANDS, main


@pytest.mark.parametrize("name", [name for name in COMMANDS if name != "api-server"])
def test_dispatch_forwards_arguments_and_exit_status(name):
    target = Mock(return_value=7)
    with patch("tue_api_wrapper.command.import_module", return_value=SimpleNamespace(main=target)) as load:
        assert main([name, "--example", "value"]) == 7
    load.assert_called_once_with(f".{COMMANDS[name][0]}", "tue_api_wrapper")
    target.assert_called_once_with(["--example", "value"])


def test_api_server_rejects_extra_arguments():
    with pytest.raises(SystemExit) as error:
        main(["api-server", "--unexpected"])
    assert error.value.code == 2
