from typing import Any, Dict, Tuple
import torch
from torchvision.models.detection.faster_rcnn import FasterRCNN, fasterrcnn_resnet50_fpn
from torchvision.transforms import transforms
from torchvision.transforms.transforms import Compose
from inference.domain.object.content import Content
from inference.helper.api_module import logger


class Detector(object):
    net: FasterRCNN
    transformer: Compose
    config: Dict[str, Any]

    def __init__(self, model_path: str):
        self.__load_model(model_path)
        self.__build_transformer()

    def predict(self, content: Content) -> Tuple[int, float]:
        x = self.transformer(content.data)
        x = x.unsqueeze(0)  # type: ignore
        x.to('cpu')
        with torch.no_grad():
            outputs = self.net(x)

        result = outputs.pop()
        is_exists = len(result['labels'])
        if is_exists > 0:
            max_confidence = 0.0
            for score in result['scores']:
                if max_confidence < score.item():  # type: ignore
                    max_confidence = score.item()  # type: ignore
            label = 1
            score: float = float('{:.3f}'.format(max_confidence))
        else:
            label = 0
            score = 0.0
        # resize_box_factors = [image.width / image_size, image.height / image_size] * 2
        # box = outputs[0]['boxes'][0]
        # resized_box = box.cpu() * torch.tensor(resize_box_factors)
        # box_xywh = resized_box[:2].tolist() + (resized_box[2:] - resized_box[:2]).tolist()
        # print(box_xywh)
        return (label, score)

    def __load_model(self, model_path: str) -> None:
        device = 'cpu'
        state_dict = torch.load(model_path, map_location=torch.device(device))
        labels_enumeration = state_dict['labels_enumeration']
        num_classes = len([key for key, val in labels_enumeration.items() if val >= 0])
        self.net = fasterrcnn_resnet50_fpn(pretrained_backbone=True, num_classes=num_classes)
        self.config = state_dict['configuration']
        self.net.load_state_dict(state_dict['model'])
        self.net.to(device)
        self.net.eval()
        logger.info(f'loading detector model: {model_path}')

    def __build_transformer(self) -> None:
        image_size = self.config['image_size']
        self.transformer = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
        ])
