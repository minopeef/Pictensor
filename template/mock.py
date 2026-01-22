import time

import asyncio
import random
import bittensor as bt

from typing import List


class MockSubtensor(bt.MockSubtensor):
    def __init__(self, netuid, n=16, wallet=None, network="mock"):
        super().__init__(network=network)

        if not self.subnet_exists(netuid):
            self.create_subnet(netuid)

        # Register ourself (the validator) as a neuron at uid=0
        if wallet is not None:
            self.force_register_neuron(
                netuid=netuid,
                hotkey=wallet.hotkey.ss58_address,
                coldkey=wallet.coldkey.ss58_address,
                balance=100000,
                stake=100000,
            )

        # Register n mock neurons who will be miners
        for i in range(1, n + 1):
            self.force_register_neuron(
                netuid=netuid,
                hotkey=f"miner-hotkey-{i}",
                coldkey="mock-coldkey",
                balance=100000,
                stake=100000,
            )


class MockMetagraph(bt.metagraph):
    def __init__(self, netuid=1, network="mock", subtensor=None):
        super().__init__(netuid=netuid, network=network, sync=False)

        if subtensor is not None:
            self.subtensor = subtensor
        self.sync(subtensor=subtensor)

        for axon in self.axons:
            axon.ip = "127.0.0.0"
            axon.port = 8091

        bt.logging.info(f"Metagraph: {self}")
        bt.logging.info(f"Axons: {self.axons}")


class MockDendrite(bt.dendrite):
    """
    Replaces a real bittensor network request with a mock request that just returns some static response for all axons that are passed and adds some random delay.
    """

    def __init__(self, wallet):
        super().__init__(wallet)
        self.min_time = 0.0
        self.max_time = 1.0

    async def forward(
        self,
        axons: List[bt.axon],
        synapse: bt.Synapse = bt.Synapse(),
        timeout: float = 12,
        deserialize: bool = True,
        run_async: bool = True,
        streaming: bool = False,
    ):
        """
        Mock forward method that simulates network requests with configurable timing.
        
        Args:
            axons: List of axons to query
            synapse: The synapse object containing request data
            timeout: Maximum time to wait for responses
            deserialize: Whether to deserialize responses
            run_async: Whether to run asynchronously
            streaming: Whether to use streaming (not implemented)
            
        Returns:
            List of response synapses
        """
        if streaming:
            raise NotImplementedError("Streaming not implemented yet.")

        async def query_all_axons():
            """Queries all axons for responses."""

            async def single_axon_response(i, axon):
                """Queries a single axon for a response."""
                start_time = time.time()
                s = synapse.copy()
                
                # Attach some more required data so it looks real
                s = self.preprocess_synapse_for_request(axon, s, timeout)
                
                # Generate random process time within configured range
                process_time = random.uniform(self.min_time, self.max_time)
                
                # Simulate processing delay
                await asyncio.sleep(process_time)
                
                actual_time = time.time() - start_time
                
                # Determine response based on timing
                if actual_time >= timeout:
                    s.dummy_output = s.dummy_input if hasattr(s, 'dummy_input') else 0
                    s.dendrite.status_code = 408
                    s.dendrite.status_message = "Timeout"
                    s.dendrite.process_time = str(actual_time)
                else:
                    # Update the status code and status message of the dendrite to match the axon
                    # TODO (developer): replace with your own expected synapse data
                    if hasattr(s, 'dummy_input'):
                        s.dummy_output = s.dummy_input * 2
                    s.dendrite.status_code = 200
                    s.dendrite.status_message = "OK"
                    s.dendrite.process_time = str(actual_time)

                # Return the updated synapse object after deserializing if requested
                if deserialize:
                    return s.deserialize()
                else:
                    return s

            return await asyncio.gather(
                *(
                    single_axon_response(i, target_axon)
                    for i, target_axon in enumerate(axons)
                )
            )

        return await query_all_axons()

    async def __call__(
        self,
        axons: List[bt.axon],
        synapse: bt.Synapse = bt.Synapse(),
        timeout: float = 12,
        deserialize: bool = True,
        run_async: bool = True,
        streaming: bool = False,
    ):
        """
        Make MockDendrite callable to match bittensor dendrite API.
        This method delegates to forward().
        """
        return await self.forward(
            axons=axons,
            synapse=synapse,
            timeout=timeout,
            deserialize=deserialize,
            run_async=run_async,
            streaming=streaming,
        )

    def __str__(self) -> str:
        """
        Returns a string representation of the Dendrite object.

        Returns:
            str: The string representation of the Dendrite object in the format "dendrite(<user_wallet_address>)".
        """
        return "MockDendrite({})".format(self.keypair.ss58_address)
