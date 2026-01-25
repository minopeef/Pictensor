import random
import bittensor as bt
import numpy as np
from typing import List, Optional


def check_uid_availability(
    metagraph: "bt.metagraph.Metagraph", uid: int, vpermit_tao_limit: int
) -> bool:
    """Check if uid is available. The UID should be available if it is serving and has less than vpermit_tao_limit stake
    Args:
        metagraph (:obj: bt.metagraph.Metagraph): Metagraph object
        uid (int): uid to be checked
        vpermit_tao_limit (int): Validator permit tao limit
    Returns:
        bool: True if uid is available, False otherwise
    """
    # Filter non serving axons.
    if not metagraph.axons[uid].is_serving:
        return False
    # Filter validator permit > 1024 stake.
    if metagraph.validator_permit[uid]:
        if metagraph.S[uid] > vpermit_tao_limit:
            return False
    # Available otherwise.
    return True


def get_random_uids(
    self, k: int, exclude: Optional[List[int]] = None
) -> np.ndarray:
    """Returns k available random uids from the metagraph.
    
    Args:
        k (int): Number of uids to return.
        exclude (Optional[List[int]]): List of uids to exclude from the random sampling.
    
    Returns:
        np.ndarray: Randomly sampled available uids.
    
    Notes:
        If `k` is larger than the number of available `uids`, set `k` to the number of available `uids`.
    """
    if exclude is None:
        exclude = []
    
    exclude_set = set(exclude)
    candidate_uids = []
    avail_uids = []
    vpermit_limit = self.config.neuron.vpermit_tao_limit

    # Single pass to collect available UIDs
    for uid in range(self.metagraph.n.item()):
        if check_uid_availability(self.metagraph, uid, vpermit_limit):
            avail_uids.append(uid)
            if uid not in exclude_set:
                candidate_uids.append(uid)
    
    # If k is larger than the number of available uids, set k to the number of available uids.
    k = min(k, len(avail_uids))
    
    if k == 0:
        return np.array([], dtype=np.int64)
    
    # Check if candidate_uids contain enough for querying, if not grab all available uids
    if len(candidate_uids) < k:
        # Add excluded but available uids to reach k
        excluded_available = [uid for uid in avail_uids if uid in exclude_set]
        needed = k - len(candidate_uids)
        if excluded_available:
            candidate_uids.extend(random.sample(excluded_available, min(needed, len(excluded_available))))
    
    # Ensure we have enough uids
    if len(candidate_uids) < k:
        k = len(candidate_uids)
    
    return np.array(random.sample(candidate_uids, k), dtype=np.int64)
