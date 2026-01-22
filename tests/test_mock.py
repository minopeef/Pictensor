# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
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

import pytest
import asyncio
import bittensor as bt
from template.mock import MockDendrite, MockMetagraph, MockSubtensor
from template.protocol import Dummy


@pytest.mark.parametrize("netuid", [1, 2, 3])
@pytest.mark.parametrize("n", [2, 4, 8, 16, 32, 64])
@pytest.mark.parametrize("wallet", [bt.MockWallet(), None])
def test_mock_subtensor(netuid, n, wallet):
    """Test MockSubtensor creation and neuron registration."""
    subtensor = MockSubtensor(netuid=netuid, n=n, wallet=wallet)
    neurons = subtensor.neurons(netuid=netuid)
    
    # Check netuid
    assert subtensor.subnet_exists(netuid)
    
    # Check network
    assert subtensor.network == "mock"
    assert subtensor.chain_endpoint == "mock_endpoint"
    
    # Check number of neurons
    expected_count = n + 1 if wallet is not None else n
    assert len(neurons) == expected_count
    
    # Check wallet registration
    if wallet is not None:
        assert subtensor.is_hotkey_registered(
            netuid=netuid, hotkey_ss58=wallet.hotkey.ss58_address
        )

    # Validate all neurons
    for neuron in neurons:
        assert isinstance(neuron, bt.NeuronInfo)
        assert subtensor.is_hotkey_registered(
            netuid=netuid, hotkey_ss58=neuron.hotkey
        )


@pytest.mark.parametrize("n", [16, 32, 64])
def test_mock_metagraph(n):
    """Test MockMetagraph creation and axon configuration."""
    mock_subtensor = MockSubtensor(netuid=1, n=n)
    mock_metagraph = MockMetagraph(subtensor=mock_subtensor)
    
    # Check axons
    axons = mock_metagraph.axons
    assert len(axons) == n
    
    # Check ip and port
    for axon in axons:
        assert isinstance(axon, bt.AxonInfo)
        assert axon.ip == mock_metagraph.default_ip
        assert axon.port == mock_metagraph.default_port


@pytest.mark.parametrize("timeout", [0.1, 0.2])
@pytest.mark.parametrize("min_time", [0, 0.05, 0.1])
@pytest.mark.parametrize("max_time", [0.1, 0.15, 0.2])
@pytest.mark.parametrize("n", [4, 16, 64])
def test_mock_dendrite_timings(timeout, min_time, max_time, n):
    """Test MockDendrite timing behavior and response handling."""
    mock_wallet = bt.MockWallet()
    mock_dendrite = MockDendrite(mock_wallet)
    
    # Set timing parameters for mock responses
    mock_dendrite.min_time = min_time
    mock_dendrite.max_time = max_time
    
    mock_subtensor = MockSubtensor(netuid=1, n=n)
    mock_metagraph = MockMetagraph(subtensor=mock_subtensor)
    axons = mock_metagraph.axons

    async def run():
        """Execute the dendrite query."""
        return await mock_dendrite.forward(
            axons=axons,
            synapse=Dummy(dummy_input=42),
            timeout=timeout,
            deserialize=True,
        )

    responses = asyncio.run(run())
    
    # Validate responses
    for synapse in responses:
        assert hasattr(synapse, "dendrite")
        assert isinstance(synapse.dendrite, bt.TerminalInfo)

        dendrite = synapse.dendrite
        
        # Check required fields
        required_fields = ("process_time", "status_code", "status_message")
        for field in required_fields:
            assert hasattr(dendrite, field)
            assert getattr(dendrite, field) is not None

        # Validate timing constraints
        process_time = float(dendrite.process_time)
        assert min_time <= process_time <= max_time + 0.1
        
        # Validate status codes based on timing
        if process_time >= timeout + 0.1:
            assert dendrite.status_code == 408
            assert dendrite.status_message == "Timeout"
            # Timeout responses should have default output (input value)
            assert synapse == 42
        elif process_time < timeout:
            assert dendrite.status_code == 200
            assert dendrite.status_message == "OK"
            # Successful responses should have processed output (input * 2)
            assert synapse == 84  # 42 * 2
