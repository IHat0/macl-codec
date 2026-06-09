import os

def configure_gpu(gpu_type: str = "cuda"):
    if gpu_type == "rocm":
        os.environ["ROCM_HOME"] = "/opt/rocm"
        os.environ["HSA_OVERRIDE_GFX_VERSION"] = "9.4.2"
        print("[GPU] 🔌 Plugged into AMD (ROCm) outlet.")
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        print("[GPU] 🔌 Plugged into NVIDIA (CUDA) outlet.")