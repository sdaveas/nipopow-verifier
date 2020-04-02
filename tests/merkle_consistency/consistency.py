"""
run with
$ python consistency.py
"""

import sys

sys.path.append("../../tools/interface/")
import contract_interface

sys.path.append("..")
from config import profiler

import pickle


def export_pkl(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def import_pkl(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)
