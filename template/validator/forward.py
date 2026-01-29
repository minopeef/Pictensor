# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Opentensor Foundation
# Copyright © 2025 Pictensor

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import bittensor as bt
from typing import TYPE_CHECKING

from template.protocol import Dummy
from template.validator.reward import get_rewards
from template.utils.uids import get_random_uids

if TYPE_CHECKING:
    from template.base.validator import BaseValidatorNeuron


async def forward(self: "BaseValidatorNeuron") -> None:
    """
    The forward function is called by the validator every time step.

    It is responsible for querying the network and scoring the responses.

    Args:
        self: The validator neuron object which contains all the necessary state for the validator.
    """
    try:
        # TODO(developer): Define how the validator selects a miner to query, how often, etc.
        # get_random_uids is an example method, but you can replace it with your own.
        miner_uids = get_random_uids(self, k=self.config.neuron.sample_size)

        if len(miner_uids) == 0:
            bt.logging.warning("No available miners to query. Skipping forward pass.")
            return

        # The dendrite client queries the network.
        responses = await self.dendrite(
            # Send the query to selected miner axons in the network.
            axons=[self.metagraph.axons[uid] for uid in miner_uids],
            # Construct a dummy query. This simply contains a single integer.
            synapse=Dummy(dummy_input=self.step),
            # All responses have the deserialize function called on them before returning.
            # You are encouraged to define your own deserialization function.
            deserialize=True,
            timeout=self.config.neuron.timeout,
        )

        # Log the results for monitoring purposes.
        bt.logging.debug(f"Received {len(responses)} responses from {len(miner_uids)} miners")

        # Define how the validator scores responses (see template/validator/reward.py).
        rewards = get_rewards(self, query=self.step, responses=responses)

        if len(rewards) > 0:
            bt.logging.debug(f"Scored responses: {rewards}")
            # Update the scores based on the rewards. You may want to define your own update_scores function for custom behavior.
            self.update_scores(rewards, miner_uids.tolist())
        else:
            bt.logging.warning("No valid rewards generated from responses.")
            
    except Exception as e:
        bt.logging.error(f"Error in forward pass: {e}")
        raise
