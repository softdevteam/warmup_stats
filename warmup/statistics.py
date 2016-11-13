import math

from kalibera import Data

CONFIDENCE = 0.99
ITERATIONS = 10000


def mean(seq):
    return math.fsum(seq) / len(seq)


def bootstrap_confidence_interval(seq, confidence=CONFIDENCE, iterations=ITERATIONS):
    size = len(seq)
    data = Data({(): seq}, [size])
    result = data.bootstrap_confidence_interval(iterations, confidence=str(confidence))
    return result.median, result.error
