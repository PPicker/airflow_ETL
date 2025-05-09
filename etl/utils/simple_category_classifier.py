from transformers import AutoProcessor, AutoModel
from PIL import Image
import torch


class FashionImageClassifier:
    def __init__(self, model_name="Marqo/marqo-fashionCLIP"):
        # self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        # self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(
            "Marqo/marqo-fashionSigLIP", trust_remote_code=True
        )
        self.processor = AutoProcessor.from_pretrained(
            "Marqo/marqo-fashionSigLIP", trust_remote_code=True
        )

        # 카테고리 분류용 텍스트 프롬프트
        self.categories = ["top", "bottom", "outerwear", "shoes"]
        self.category_features = self._embed_texts(self.categories)

        # 시점(view) 분류용 텍스트 프롬프트
        self.views = ["a front of clothing", "a back of clothing", "a side of clothing"]
        self.view_features = self._embed_texts(self.views)

    def _embed_texts(self, texts):
        with torch.no_grad():
            inputs = self.processor(
                text=texts, return_tensors="pt", padding="max_length", truncation=True
            )
            return self.model.get_text_features(**inputs, normalize=True)

    def _embed_image(self, image_path):
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            return self.model.get_image_features(**inputs, normalize=True)

    def _classify(self, image_features, text_features, labels):
        probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        predicted_index = torch.argmax(probs, dim=-1).item()
        predicted_label = labels[predicted_index]
        confidence = probs[0, predicted_index].item()
        return predicted_label, confidence

    def classify_category(self, image_path):
        image_features = self._embed_image(image_path)
        return self._classify(image_features, self.category_features, self.categories)

    def classify_view(self, image_path):
        image_features = self._embed_image(image_path)
        return self._classify(image_features, self.view_features, self.views)


if __name__ == "__main__":
    classifier = FashionImageClassifier()
