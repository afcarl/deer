#! /usr/bin/env python
"""
Execute a training run of general deep-Q-Leaning with following parameters:

"""

import launcher
import sys

class Defaults:
    # ----------------------
    # Experiment Parameters
    # ----------------------
    STEPS_PER_EPOCH = 365*24-5
    EPOCHS = 1000
    STEPS_PER_TEST = 365*24-5
    PERIOD_BTW_SUMMARY_PERFS = 10
    
    # ----------------------
    # Environment Parameters
    # ----------------------
    ENV_PATH = "MG_two_storages"
    FRAME_SKIP = 1#4

    # ----------------------
    # DQN Agent parameters:
    # ----------------------
    UPDATE_RULE = 'deepmind_rmsprop'#'deepmind_rmsprop'
    BATCH_ACCUMULATOR = 'sum'
    LEARNING_RATE = 0.0002#TOY_ENV:0.0002
    LEARNING_RATE_DECAY = 1. #TOY_ENV:1.
    DISCOUNT = 0.9#TOY_ENV:0.9
    DISCOUNT_INC = 1.#TOY_ENV:1.#0.99
    
    RMS_DECAY = 0.9#.99 # (Rho)
    RMS_EPSILON = 0.0001#.01
    MOMENTUM = 0 # Note that the "momentum" value mentioned in the Nature
                 # paper is not used in the same way as a traditional momentum
                 # term.  It is used to track gradient for the purpose of
                 # estimating the standard deviation. This package uses
                 # rho/RMS_DECAY to track both the history of the gradient
                 # and the squared gradient.
    CLIP_DELTA = 1.0
    EPSILON_START = 1.0
    EPSILON_MIN = .3#.1
    EPSILON_DECAY = 5000000
    UPDATE_FREQUENCY = 1#4
    REPLAY_MEMORY_SIZE = 1000000
    BATCH_SIZE = 32
    NETWORK_TYPE = "General_DQN_0"
    FREEZE_INTERVAL = 1000#10000#10000
    REPLAY_START_SIZE = 5#50000 --> that many action before using non random action
    MAX_START_NULLOPS = 5#30
    DETERMINISTIC = True
    CUDNN_DETERMINISTIC = False

if __name__ == "__main__":
    launcher.launch(sys.argv[1:], Defaults, __doc__)