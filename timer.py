import time

class Timer:
    def __init__(self):
        self.start=time.time()

    def __del__(self):
        print('Time elapsed:', time.time() - self.start)
