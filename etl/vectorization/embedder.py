import pandas as pd
from torch import no_grad

# from transformers import AutoProcessor, AutoModel
# from transformers import CLIPModel, CLIPProcessor
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
from typing import List
import torch
from torch.nn import functional as F
import functools


def normalize_output(fn):
    """임베딩 결과를, self.normalize가 True일 때만 L2 정규화해서 리턴해 주는 데코레이터"""

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        feats = fn(self, *args, **kwargs)
        if getattr(self, "normalize", False):
            # L2 노름으로 정규화 (마지막 차원 기준)
            eps = 1e-12
            normed = feats / feats.norm(p=2, dim=-1, keepdim=True).clamp_min(eps)
            return normed
        return feats

    return wrapper


class Embedding_Model:
    def __init__(self, model_name="patrickjohncyh/fashion-clip", normalize=True):
        self.model_name = model_name
        self.normalize = normalize
        self.embedder = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.embedder.eval()
        self.embedder.float()
        self.dim = 512

    @normalize_output
    @torch.inference_mode()
    def embed_images(self, all_images):
        # 한 번에 이미지 임베딩 계산 (배치 처리)
        inputs = self.processor(images=all_images, return_tensors="pt", padding=True)
        embeddings = self.embedder.get_image_features(**inputs)
        return embeddings

    @normalize_output
    @torch.inference_mode()
    def embed_image(self, image):
        inputs = self.processor(images=image, return_tensors="pt")
        embedding = self.embedder.get_image_features(**inputs)
        return embedding.squeeze(0)

    # 텍스트 임베딩 함수
    @normalize_output
    @torch.inference_mode()
    def embed_text(self, text, max_length=77):
        inputs = self.processor(
            text=[text],
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )
        embedding = self.embedder.get_text_features(**inputs)
        return embedding.squeeze(0)


if __name__ == "__main__":
    model = Embedding_Model()
    model.embed_text("hi")
