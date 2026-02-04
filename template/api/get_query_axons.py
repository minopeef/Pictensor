# The MIT License (MIT)
# Copyright © 2021 Yuma Rao
# Copyright © 2023 Opentensor Foundation
# Copyright © 2023 Opentensor Technologies Inc
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

from typing import List, Optional, Union

import numpy as np
import random
import bittensor as bt


async def ping_uids(
    dendrite: "bt.dendrite",
    metagraph: "bt.metagraph",
    uids: List[int],
    timeout: float = 3,
) -> tuple:
    """
    Pings a list of UIDs to check their availability on the Bittensor network.

    Args:
        dendrite: The dendrite instance to use for pinging nodes.
        metagraph: The metagraph instance containing network information.
        uids: A list of UIDs (unique identifiers) to ping.
        timeout (int, optional): The timeout in seconds for each ping. Defaults to 3.

    Returns:
        tuple: A tuple containing two lists:
            - The first list contains UIDs that were successfully pinged.
            - The second list contains UIDs that failed to respond.
    """
    axons = [metagraph.axons[uid] for uid in uids]
    try:
        responses = await dendrite(
            axons,
            bt.Synapse(),  # TODO: potentially get the synapses available back?
            deserialize=False,
            timeout=timeout,
        )
        successful_uids = [
            uid
            for uid, response in zip(uids, responses)
            if response.dendrite.status_code == 200
        ]
        failed_uids = [
            uid
            for uid, response in zip(uids, responses)
            if response.dendrite.status_code != 200
        ]
    except Exception as e:
        bt.logging.error(f"Dendrite ping failed: {e}")
        successful_uids = []
        failed_uids = uids
    bt.logging.debug(f"ping() successful uids: {successful_uids}")
    bt.logging.debug(f"ping() failed uids    : {failed_uids}")
    return successful_uids, failed_uids

async def get_query_api_nodes(
    dendrite: "bt.dendrite",
    metagraph: "bt.metagraph",
    n: float = 0.1,
    timeout: float = 3,
) -> List[int]:
    """
    Fetches the available API nodes to query for the particular subnet.

    Args:
        dendrite: The dendrite instance to use for pinging nodes.
        metagraph: The metagraph instance containing network information.
        n: The fraction of top nodes to consider based on stake. Defaults to 0.1.
        timeout: The timeout in seconds for pinging nodes. Defaults to 3.

    Returns:
        A list of UIDs representing the available API nodes.
    """
    bt.logging.debug(
        f"Fetching available API nodes for subnet {metagraph.netuid}"
    )
    vtrust_uids = [
        uid.item()
        for uid in metagraph.uids
        if metagraph.validator_trust[uid] > 0
    ]
    top_uids = np.where(metagraph.S > np.quantile(metagraph.S, 1 - n))[0].tolist()
    init_query_uids = set(top_uids).intersection(set(vtrust_uids))
    query_uids, _ = await ping_uids(
        dendrite, metagraph, list(init_query_uids), timeout=timeout
    )
    bt.logging.debug(
        f"Available API node UIDs for subnet {metagraph.netuid}: {query_uids}"
    )
    if len(query_uids) > 3:
        query_uids = random.sample(query_uids, 3)
    return query_uids


async def get_query_api_axons(
    wallet: "bt.wallet",
    metagraph: Optional["bt.metagraph"] = None,
    n: float = 0.1,
    timeout: float = 3,
    uids: Optional[Union[List[int], int]] = None,
) -> list:
    """
    Retrieves the axons of query API nodes based on their availability and stake.

    Args:
        wallet: The wallet instance to use for querying nodes.
        metagraph: The metagraph instance containing network information. Uses template default netuid if None.
        n: The fraction of top nodes to consider based on stake. Defaults to 0.1.
        timeout: The timeout in seconds for pinging nodes. Defaults to 3.
        uids: The specific UID(s) of the API node(s) to query. Defaults to None.

    Returns:
        A list of axon objects for the available API nodes.
    """
    dendrite = bt.dendrite(wallet=wallet)

    if metagraph is None:
        metagraph = bt.metagraph(netuid=1)  # Template default netuid

    if uids is not None:
        query_uids = [uids] if isinstance(uids, int) else uids
    else:
        query_uids = await get_query_api_nodes(
            dendrite, metagraph, n=n, timeout=timeout
        )
    return [metagraph.axons[uid] for uid in query_uids]
