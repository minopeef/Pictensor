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

"""
Example API client for Storage Subnet 21.
Requires the storage-subnet package: https://github.com/ifrit98/storage-subnet
"""

import base64
import bittensor as bt
from typing import Any, List, Union

from bittensor.subnets import SubnetsAPI

try:
    from storage.validator.cid import generate_cid_string
    from storage.validator.encryption import (
        encrypt_data,
        decrypt_data_with_private_key,
    )
    from storage.validator.protocol import StoreUser, RetrieveUser
except ImportError:
    storage_url = "https://github.com/ifrit98/storage-subnet"
    bt.logging.warning(
        f"Storage Subnet 21 not installed. Install the package to use this example: {storage_url}"
    )
    generate_cid_string = None
    encrypt_data = None
    decrypt_data_with_private_key = None
    StoreUser = None  # type: ignore[misc, assignment]
    RetrieveUser = None  # type: ignore[misc, assignment]


class StoreUserAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 21

    def prepare_synapse(
        self,
        data: bytes,
        encrypt: bool = False,
        ttl: int = 60 * 60 * 24 * 30,
        encoding: str = "utf-8",
    ) -> Any:
        if StoreUser is None:
            raise RuntimeError(
                "Storage subnet package not installed. Install from https://github.com/ifrit98/storage-subnet"
            )
        data = bytes(data, encoding) if isinstance(data, str) else data
        encrypted_data, encryption_payload = (
            encrypt_data(data, self.wallet) if encrypt else (data, "{}")
        )
        expected_cid = generate_cid_string(encrypted_data)
        encoded_data = base64.b64encode(encrypted_data)

        synapse = StoreUser(
            encrypted_data=encoded_data,
            encryption_payload=encryption_payload,
            ttl=ttl,
        )

        return synapse

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> str:
        success = False
        failure_modes = {"code": [], "message": []}
        for response in responses:
            if response.dendrite.status_code != 200:
                failure_modes["code"].append(response.dendrite.status_code)
                failure_modes["message"].append(
                    response.dendrite.status_message
                )
                continue

            stored_cid = (
                response.data_hash.decode("utf-8")
                if isinstance(response.data_hash, bytes)
                else response.data_hash
            )
            bt.logging.debug("received data CID: {}".format(stored_cid))
            success = True
            break

        if success:
            bt.logging.info(
                f"Stored data on the Bittensor network with CID {stored_cid}"
            )
        else:
            bt.logging.error(
                f"Failed to store data. Response failure codes & messages {failure_modes}"
            )
            stored_cid = ""

        return stored_cid


class RetrieveUserAPI(SubnetsAPI):
    def __init__(self, wallet: "bt.wallet"):
        super().__init__(wallet)
        self.netuid = 21

    def prepare_synapse(self, cid: str) -> Any:
        if RetrieveUser is None:
            raise RuntimeError(
                "Storage subnet package not installed. Install from https://github.com/ifrit98/storage-subnet"
            )
        synapse = RetrieveUser(data_hash=cid)
        return synapse

    def process_responses(
        self, responses: List[Union["bt.Synapse", Any]]
    ) -> bytes:
        success = False
        decrypted_data = b""
        for response in responses:
            bt.logging.trace(f"response: {response.dendrite.dict()}")
            if (
                response.dendrite.status_code != 200
                or response.encrypted_data is None
            ):
                continue

            # Decrypt the response
            bt.logging.trace(
                f"encrypted_data: {response.encrypted_data[:100]}"
            )
            encrypted_data = base64.b64decode(response.encrypted_data)
            bt.logging.debug(
                f"encryption_payload: {response.encryption_payload}"
            )
            if (
                response.encryption_payload is None
                or response.encryption_payload == ""
                or response.encryption_payload == "{}"
            ):
                bt.logging.warning(
                    "No encryption payload found. Unencrypted data."
                )
                decrypted_data = encrypted_data
            else:
                decrypted_data = decrypt_data_with_private_key(
                    encrypted_data,
                    response.encryption_payload,
                    bytes(self.wallet.coldkey.private_key.hex(), "utf-8"),
                )
            bt.logging.trace(f"decrypted_data: {decrypted_data[:100]}")
            success = True
            break

        if success:
            bt.logging.info(
                f"Returning retrieved data: {decrypted_data[:100]}"
            )
        else:
            bt.logging.error("Failed to retrieve data.")

        return decrypted_data


async def test_store_and_retrieve(
    netuid: int = 22, wallet: "bt.wallet" = None
):
    # Example usage
    wallet = wallet or bt.wallet()

    # Instantiate the handler
    store_handler = StoreUserAPI(wallet)

    # Fetch the axons you want to query
    metagraph = bt.subtensor("test").metagraph(netuid=netuid)
    query_axons = metagraph.axons

    cid = await store_handler(
        axons=query_axons,
        # any arguments for the proper synapse
        data=b"some data",
        encrypt=True,
        ttl=60 * 60 * 24 * 30,
        encoding="utf-8",
        uid=None,
    )
    print("CID:", cid)

    retrieve_handler = RetrieveUserAPI(wallet)
    retrieve_response = await retrieve_handler(axons=query_axons, cid=cid)
