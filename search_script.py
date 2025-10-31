import os
from comfyfixersmart.config import config
from comfyfixersmart.search import ModelSearch

config.comfyui_root = "/home/coldaine/StableDiffusionWorkflow/ComfyUI-stable"
config.search.backend_order = ["civitai"]

search = ModelSearch()
result = search.search_model({'filename': 'Ana_de_Armas_FLUX_v1-000061.safetensors'})
print(result.__dict__)