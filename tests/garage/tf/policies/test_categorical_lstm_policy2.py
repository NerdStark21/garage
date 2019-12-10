import pickle

import numpy as np
import pytest
import tensorflow as tf

from garage.tf.envs import TfEnv
from garage.tf.policies import CategoricalLSTMPolicy2
from tests.fixtures import TfGraphTestCase
from tests.fixtures.envs.dummy import DummyBoxEnv
from tests.fixtures.envs.dummy import DummyDiscreteEnv


class TestCategoricalLSTMPolicy2(TfGraphTestCase):

    def test_invalid_env(self):
        env = TfEnv(DummyBoxEnv())
        with pytest.raises(ValueError):
            CategoricalLSTMPolicy2(env_spec=env.spec)

    @pytest.mark.parametrize('obs_dim, action_dim, hidden_dim', [
        ((1, ), 1, 4),
        ((2, ), 2, 4),
        ((1, 1), 1, 4),
        ((2, 2), 2, 4),
    ])
    def test_get_action_state_include_action(self, obs_dim, action_dim,
                                             hidden_dim):
        env = TfEnv(DummyDiscreteEnv(obs_dim=obs_dim, action_dim=action_dim))
        obs_var = tf.compat.v1.placeholder(
            tf.float32,
            shape=[None, None, env.observation_space.flat_dim + action_dim],
            name='obs')
        policy = CategoricalLSTMPolicy2(env_spec=env.spec,
                                        hidden_dim=hidden_dim,
                                        state_include_action=True)

        policy.build(obs_var)
        policy.reset()
        obs = env.reset()

        action, _ = policy.get_action(obs.flatten())
        assert env.action_space.contains(action)

        actions, _ = policy.get_actions([obs.flatten()])
        for action in actions:
            assert env.action_space.contains(action)

    @pytest.mark.parametrize('obs_dim, action_dim, hidden_dim', [
        ((1, ), 1, 4),
        ((2, ), 2, 4),
        ((1, 1), 1, 4),
        ((2, 2), 2, 4),
    ])
    def test_get_action(self, obs_dim, action_dim, hidden_dim):
        env = TfEnv(DummyDiscreteEnv(obs_dim=obs_dim, action_dim=action_dim))
        obs_var = tf.compat.v1.placeholder(
            tf.float32,
            shape=[None, None, env.observation_space.flat_dim],
            name='obs')
        policy = CategoricalLSTMPolicy2(env_spec=env.spec,
                                        hidden_dim=hidden_dim,
                                        state_include_action=False)

        policy.build(obs_var)
        policy.reset()
        obs = env.reset()

        action, _ = policy.get_action(obs.flatten())
        assert env.action_space.contains(action)

        actions, _ = policy.get_actions([obs.flatten()])
        for action in actions:
            assert env.action_space.contains(action)

    def test_is_pickleable(self):
        env = TfEnv(DummyDiscreteEnv(obs_dim=(1, ), action_dim=1))
        obs_var = tf.compat.v1.placeholder(
            tf.float32,
            shape=[None, None, env.observation_space.flat_dim],
            name='obs')
        policy = CategoricalLSTMPolicy2(env_spec=env.spec,
                                        state_include_action=False)

        policy.build(obs_var)
        policy.reset()
        obs = env.reset()

        policy.model._lstm_cell.weights[0].load(
            tf.ones_like(policy.model._lstm_cell.weights[0]).eval())

        output1 = self.sess.run(
            [policy.distribution.logits],
            feed_dict={policy.model.input: [[obs.flatten()], [obs.flatten()]]})

        p = pickle.dumps(policy)

        with tf.compat.v1.Session(graph=tf.Graph()) as sess:
            policy_pickled = pickle.loads(p)
            obs_var = tf.compat.v1.placeholder(
                tf.float32,
                shape=[None, None, env.observation_space.flat_dim],
                name='obs')
            policy_pickled.build(obs_var)
            output2 = sess.run([policy_pickled.distribution.logits],
                               feed_dict={
                                   policy_pickled.model.input:
                                   [[obs.flatten()], [obs.flatten()]]
                               })  # noqa: E126
            assert np.array_equal(output1, output2)
