# The MIT License (MIT)
# Copyright © 2023 Opentensor Foundation

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from typing import Union
from bittensor import (
    Balance,
    NeuronInfo,
    AxonInfo,
    PrometheusInfo,
    __ss58_format__,
)
from bittensor.mock.wallet_mock import MockWallet as _MockWallet
from bittensor.mock.wallet_mock import get_mock_coldkey as _get_mock_coldkey
from bittensor.mock.wallet_mock import get_mock_hotkey as _get_mock_hotkey
from bittensor.mock.wallet_mock import get_mock_keypair as _get_mock_keypair
from bittensor.mock.wallet_mock import get_mock_wallet as _get_mock_wallet

from rich.console import Console
from rich.text import Text


def __mock_wallet_factory__(*args, **kwargs) -> _MockWallet:
    """Returns a mock wallet object."""
    return _get_mock_wallet()


class CLOSE_IN_VALUE:
    """Helper class for approximate value comparison in tests."""
    
    def __init__(
        self,
        value: Union[float, int, Balance],
        tolerance: Union[float, int, Balance] = 0.0,
    ) -> None:
        """
        Initialize with a value and optional tolerance.
        
        Args:
            value: The expected value
            tolerance: The acceptable tolerance range
        """
        self.value = value
        self.tolerance = tolerance

    def __eq__(self, other: Union[float, int, Balance]) -> bool:
        """
        Check if other value is within tolerance range.
        
        Args:
            other: The value to compare
            
        Returns:
            True if values are within tolerance, False otherwise
        """
        # True if other is in [value - tolerance, value + tolerance]
        # or if value is in [other - tolerance, other + tolerance]
        return (
            (self.value - self.tolerance) <= other
            and other <= (self.value + self.tolerance)
        ) or (
            (other - self.tolerance) <= self.value
            and self.value <= (other + self.tolerance)
        )


def get_mock_neuron(**kwargs) -> NeuronInfo:
    """
    Returns a mock neuron with the given kwargs overriding the default values.
    
    Args:
        **kwargs: Keyword arguments to override default neuron values
        
    Returns:
        NeuronInfo: A mock neuron object
    """
    mock_neuron_d = {
        "netuid": -1,  # mock netuid
        "axon_info": AxonInfo(
            block=0,
            version=1,
            ip=0,
            port=0,
            ip_type=0,
            protocol=0,
            placeholder1=0,
            placeholder2=0,
        ),
        "prometheus_info": PrometheusInfo(
            block=0, version=1, ip=0, port=0, ip_type=0
        ),
        "validator_permit": True,
        "uid": 1,
        "hotkey": "some_hotkey",
        "coldkey": "some_coldkey",
        "active": 0,
        "last_update": 0,
        "stake": {"some_coldkey": 1e12},
        "total_stake": 1e12,
        "rank": 0.0,
        "trust": 0.0,
        "consensus": 0.0,
        "validator_trust": 0.0,
        "incentive": 0.0,
        "dividends": 0.0,
        "emission": 0.0,
        "bonds": [],
        "weights": [],
        "stake_dict": {},
        "pruning_score": 0.0,
        "is_null": False,
    }

    mock_neuron_d.update(kwargs)  # update with kwargs

    # Auto-calculate stake if coldkey is provided
    if kwargs.get("stake") is None and kwargs.get("coldkey") is not None:
        mock_neuron_d["stake"] = {kwargs.get("coldkey"): 1e12}

    # Auto-calculate total_stake if not provided
    if kwargs.get("total_stake") is None:
        mock_neuron_d["total_stake"] = sum(mock_neuron_d["stake"].values())

    mock_neuron = NeuronInfo._neuron_dict_to_namespace(mock_neuron_d)

    return mock_neuron


def get_mock_neuron_by_uid(uid: int, **kwargs) -> NeuronInfo:
    """
    Returns a mock neuron for a specific UID.
    
    Args:
        uid: The UID for the neuron
        **kwargs: Additional keyword arguments to override defaults
        
    Returns:
        NeuronInfo: A mock neuron object with the specified UID
    """
    return get_mock_neuron(
        uid=uid,
        hotkey=_get_mock_hotkey(uid),
        coldkey=_get_mock_coldkey(uid),
        **kwargs
    )


class MockStatus:
    """Mock status object for testing rich console output."""
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def start(self):
        """Start the status display."""
        pass

    def stop(self):
        """Stop the status display."""
        pass

    def update(self, *args, **kwargs):
        """Update the status display."""
        MockConsole().print(*args, **kwargs)


class MockConsole:
    """
    Mocks the console object for status and print operations.
    Captures the last print output as a string.
    """

    captured_print = None

    def status(self, *args, **kwargs):
        """Return a mock status object."""
        return MockStatus()

    def print(self, *args, **kwargs):
        """
        Capture print output for testing.
        
        Args:
            *args: Arguments to print
            **kwargs: Keyword arguments for print
        """
        console = Console(
            width=1000, no_color=True, markup=False
        )  # set width to 1000 to avoid truncation
        console.begin_capture()
        console.print(*args, **kwargs)
        self.captured_print = console.end_capture()

    def clear(self, *args, **kwargs):
        """Clear the console (no-op for mock)."""
        pass

    @staticmethod
    def remove_rich_syntax(text: str) -> str:
        """
        Removes rich syntax from the given text.
        Removes markup and ansi syntax.
        
        Args:
            text: Text with rich syntax
            
        Returns:
            Plain text without rich syntax
        """
        output_no_syntax = Text.from_ansi(Text.from_markup(text).plain).plain
        return output_no_syntax
