import numpy as np

def smooth_array(data: np.ndarray, kernel = None, kernel_size: int | None = 50) -> np.ndarray:
    """data must be in shape (channels, datapoints)"""

    if kernel is None and kernel_size is None:
        raise Exception('Either kernel or kernel_size must be not None')
    
    if kernel is None:

        sides = np.ones((kernel_size // 2,)) / (2 * kernel_size)

        kernel = np.concat([sides, np.array([0.5]), sides])

    smoothed = np.apply_along_axis(lambda x: np.convolve(x, kernel, mode='same'), axis=1, arr=data)

    return smoothed
