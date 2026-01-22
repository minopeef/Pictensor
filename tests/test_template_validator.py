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

import unittest
import torch
import numpy as np
import bittensor as bt

from neurons.validator import Validator
from template.base.validator import BaseValidatorNeuron
from template.protocol import Dummy
from template.utils.uids import get_random_uids
from template.validator.reward import get_rewards


class TemplateValidatorNeuronTestCase(unittest.TestCase):
    """
    Unit tests for the Template Validator Neuron.
    
    Tests cover validator initialization, forward pass, response handling,
    and reward calculation scenarios.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock configuration
        config = BaseValidatorNeuron.config()
        config.wallet._mock = True
        config.metagraph._mock = True
        config.subtensor._mock = True
        config.neuron.sample_size = 10
        
        self.neuron = Validator(config)
        self.miner_uids = get_random_uids(self.neuron, k=10)

    def tearDown(self):
        """Clean up after each test method."""
        if hasattr(self.neuron, 'close'):
            self.neuron.close()

    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        self.assertIsNotNone(self.neuron)
        self.assertIsNotNone(self.neuron.wallet)
        self.assertIsNotNone(self.neuron.metagraph)
        self.assertIsNotNone(self.neuron.dendrite)
        self.assertIsNotNone(self.neuron.subtensor)

    def test_dummy_responses(self):
        """Test that dummy responses are correctly constructed and processed."""
        test_input = 42
        responses = self.neuron.dendrite.query(
            axons=[self.neuron.metagraph.axons[uid] for uid in self.miner_uids],
            synapse=Dummy(dummy_input=test_input),
            deserialize=True,
        )

        # Validate all responses
        self.assertEqual(len(responses), len(self.miner_uids))
        for response in responses:
            # Expected output is input * 2
            self.assertEqual(response, test_input * 2)

    def test_reward_calculation(self):
        """Test that reward function returns correct values."""
        test_input = 42
        responses = self.neuron.dendrite.query(
            axons=[self.neuron.metagraph.axons[uid] for uid in self.miner_uids],
            synapse=Dummy(dummy_input=test_input),
            deserialize=True,
        )

        rewards = get_rewards(self.neuron, query=test_input, responses=responses)
        
        # All correct responses should receive reward of 1.0
        expected_rewards = np.ones(len(responses), dtype=np.float32)
        np.testing.assert_array_equal(rewards, expected_rewards)

    def test_reward_with_nan(self):
        """Test that NaN rewards are correctly sanitized."""
        test_input = 42
        responses = self.neuron.dendrite.query(
            axons=[self.neuron.metagraph.axons[uid] for uid in self.miner_uids],
            synapse=Dummy(dummy_input=test_input),
            deserialize=True,
        )

        rewards = get_rewards(self.neuron, query=test_input, responses=responses)
        
        # Introduce NaN value
        rewards_with_nan = rewards.copy()
        rewards_with_nan[0] = float("nan")

        # Test that update_scores handles NaN gracefully
        with self.assertLogs(bt.logging, level="WARNING") as log_context:
            self.neuron.update_scores(rewards_with_nan, self.miner_uids)
        
        # Verify warning was logged
        self.assertTrue(len(log_context.output) > 0)

    def test_reward_with_incorrect_responses(self):
        """Test reward calculation with incorrect responses."""
        test_input = 42
        # Create responses with some incorrect values
        responses = [84, 84, 100, 84, 50]  # Some correct, some incorrect
        
        rewards = get_rewards(self.neuron, query=test_input, responses=responses)
        
        # Check that correct responses get 1.0 and incorrect get 0.0
        expected_rewards = np.array([1.0, 1.0, 0.0, 1.0, 0.0], dtype=np.float32)
        np.testing.assert_array_equal(rewards, expected_rewards)

    def test_get_random_uids(self):
        """Test that get_random_uids returns valid UIDs."""
        uids = get_random_uids(self.neuron, k=5)
        
        self.assertEqual(len(uids), 5)
        self.assertTrue(all(isinstance(uid, int) for uid in uids))
        self.assertTrue(all(0 <= uid < len(self.neuron.metagraph.axons) for uid in uids))
        
        # Check for uniqueness
        self.assertEqual(len(uids), len(set(uids)))

    @unittest.skip("TODO: Implement test for single step execution")
    def test_run_single_step(self):
        """Test a single step execution."""
        pass

    @unittest.skip("TODO: Implement test for registration validation")
    def test_sync_error_if_not_registered(self):
        """Test that the validator throws an error if it is not registered on metagraph."""
        pass

    @unittest.skip("TODO: Implement test for forward function")
    def test_forward(self):
        """Test that the forward function returns the correct value."""
        pass
