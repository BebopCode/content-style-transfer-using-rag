import cupy as cp

print("CuPy version:", cp.__version__)
print("CUDA/ROCm available:", cp.is_available())
print("Device name:", cp.cuda.runtime.getDeviceProperties(0)['name'])
