import sys
sys.path.insert(0,"./")
from common import FinalImage, Screen, LatitudeRef, LongitudeRef, Corner
from datetime import datetime
from typing import List
from PIL import Image

class Store:
    _instance = None
    current_screen: Screen = Screen.HOME
    images: List[str] = []
    _final_images: List[FinalImage] = []
    datetime: datetime = None
    latitude_deg: float = None
    latitude_ref: LatitudeRef = LatitudeRef.N
    longitude_deg: float = None
    longitude_ref: LongitudeRef = LongitudeRef.E
    address: str = None
    pic_name: str = None
    from_minutes: int = 0
    to_minutes: int = 0
    corner: Corner = Corner.BOTTOM_RIGHT
    
    def __new__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super(Store, self).__new__(self, *args, **kwargs)
        return self._instance

    def get_dict(self):
        return {
            "images": self.images,
            "datetime": self.datetime,
            "latitude": {
                "deg": self.latitude_deg,
                "ref": self.latitude_ref
            },
            "longitude": {
                "deg": self.longitude_deg,
                "ref": self.longitude_ref
            },
            "address": self.address
        }
        
    def insert_final_image(self, image_path: str, image: Image.Image, exif_bytes: bytes):
        self._final_images.append(FinalImage(image_path=image_path, image=image, exif_bytes=exif_bytes))
        
    def get_final_images(self):
        return self._final_images

    def __repr__(self):
        return self.get_dict()
    
    def reset(self):
        self._instance = Store()
