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

import typing

import bittensor as bt

from template.base.miner import BaseMinerNeuron
from template.protocol import Dummy


class Miner(BaseMinerNeuron):
    """
    Miner neuron: processes requests from validators and returns responses.

    Override :meth:`forward` with your protocol logic. Customize :meth:`blacklist`
    and :meth:`priority` for security and request ordering. Base setup (wallet,
    subtensor, metagraph, logging) is handled by BaseMinerNeuron and BaseNeuron.
    """

    def __init__(self, config=None):
        super().__init__(config=config)
        # Add any use-case-specific initialization here.

    async def forward(self, synapse: Dummy) -> Dummy:
        """
        Process an incoming Dummy synapse and set the response.

        Replace this with your protocol logic. Example: set ``synapse.dummy_output``
        from ``synapse.dummy_input`` (or your protocol fields).
        """
        # Replace with your protocol logic.
        synapse.dummy_output = synapse.dummy_input * 2
        return synapse

    async def blacklist(self, synapse: Dummy) -> typing.Tuple[bool, str]:
        """
        Return (True, reason) to reject a request, (False, reason) to allow it.

        Runs before deserialization. Check metagraph registration and
        validator_permit when you need to restrict who can query the miner.
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            bt.logging.warning("Request missing dendrite or hotkey.")
            return True, "Missing dendrite or hotkey"

        hotkey = synapse.dendrite.hotkey
        if not self.config.blacklist.allow_non_registered:
            if hotkey not in self.metagraph.hotkeys:
                bt.logging.trace(f"Blacklisting un-registered hotkey {hotkey}")
                return True, "Unrecognized hotkey"

        if self.config.blacklist.force_validator_permit:
            try:
                uid = self.metagraph.hotkeys.index(hotkey)
                if not self.metagraph.validator_permit[uid]:
                    bt.logging.warning(
                        f"Blacklisting non-validator hotkey {hotkey}"
                    )
                    return True, "Non-validator hotkey"
            except ValueError:
                return True, "Unrecognized hotkey"

        bt.logging.trace(f"Allowing hotkey {hotkey}")
        return False, "Hotkey recognized!"

    async def priority(self, synapse: Dummy) -> float:
        """
        Return a priority value for the request; higher = processed first.

        Default: use caller stake from the metagraph. Override for custom logic.
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            return 0.0
        try:
            uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            p = float(self.metagraph.S[uid])
            bt.logging.trace(
                f"Priority for {synapse.dendrite.hotkey}: {p}"
            )
            return p
        except ValueError:
            return 0.0


if __name__ == "__main__":
    miner = Miner()
    miner.run()
