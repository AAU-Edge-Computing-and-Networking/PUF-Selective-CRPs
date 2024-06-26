# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 14:28:44 2024

@author: Mieszko Ferens

Script to run simulation for evaluating reliability of Binary-coded with
Padding (BP) CRP subsets.
"""

import argparse
import pandas as pd
from pathlib import Path

import numpy as np
from pypuf.simulation import XORArbiterPUF

class ChallengeResponseSet():
    def __init__(self, n, challenges, responses):
        self.challenge_length = n
        self.challenges = challenges
        self.responses = np.expand_dims(
            np.expand_dims(responses,axis=1),axis=1)

def create_binary_code_challenges(n, N):
    
    n_bits = 16
    lsb = np.arange(2**n_bits, dtype=np.uint8).reshape(-1,1)
    msb = lsb.copy()
    msb.sort(axis=0)

    lsb = np.unpackbits(lsb, axis=1)[:,-8:].copy()
    msb = np.unpackbits(msb, axis=1)[:,-8:].copy()

    challenges = 2*np.concatenate((msb,lsb), axis=1, dtype=np.int8) - 1
    for i in range(int(np.sqrt(n/n_bits))):
        challenges = np.insert(
            challenges, range(1,((2**i)*n_bits)+1), -1, axis=1)
    
    shift = challenges.copy()
    for i in range(1, int(n/n_bits)):
        challenges = np.append(challenges, np.roll(shift, i, axis=1), axis=0)
    
    _ , idx = np.unique(challenges, return_index=True, axis=0)
    challenges = challenges[np.sort(idx)]
    
    assert N <= len(challenges), (
        "Not enough CRPs have been generated. The limit is 2^18 - 3 CRPs.")
    challenges = challenges[:N]
    
    return challenges

def main():
    
    # Set-up logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=str, default="./Results/")
    parser.add_argument("--seed", type=int, default=0, help="Random seed.")
    parser.add_argument("--n-bits", type=int, default=64,
                        help="Challenge length in bits.")
    parser.add_argument("--k", type=int, default=1,
                        help="The number of parallel APUF in the XOR PUF.")
    parser.add_argument("--n-CRPs", type=int, default=2**16,
                        help="Number of CRPs to be generated.")
    parser.add_argument("--n-evals", type=int, default=10,
                        help="Number of repeated noisy measurements.")
    parser.add_argument("--noise", type=float, default=0.1,
                        help="Noise factor added to PUF parameters.")
    args = parser.parse_args()
    
    # Generate the PUF
    puf0 = XORArbiterPUF(args.n_bits, args.k, args.seed)
    pufN = XORArbiterPUF(args.n_bits, args.k, args.seed, noisiness=args.noise)
    
    # Generate the challenges
    challenges = create_binary_code_challenges(n=args.n_bits, N=args.n_CRPs)
    
    # Get responses
    responses = puf0.eval(challenges)
    
    # Calculate reliability of responses
    errors = []
    for i in range(args.n_evals):
        errors.append(np.count_nonzero(responses - pufN.eval(challenges)))
    reliability = sum(errors)/(args.n_CRPs*args.n_evals)
    
    # Log data into csv format
    data = pd.DataFrame({"seed": [args.seed],
                         "n_bits": [args.n_bits],
                         "k": [args.k],
                         "n_CRPs": [args.n_CRPs],
                         "noise": [args.noise],
                         "reliability": [reliability]})
    filepath = Path(args.outdir + "out_rel_regular_pattern_" + str(args.k) +
                    "XOR.csv")
    if(filepath.is_file()):
        data.to_csv(filepath, header=False, index=False, mode='a')
    else:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(filepath, header=True, index=False, mode='a')
    

if(__name__ == "__main__"):
    main()
