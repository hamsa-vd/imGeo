import sys
sys.path.insert(0,"./")
from common import FinalImage, Screen, LatitudeRef, LongitudeRef
from datetime import datetime
from typing import List
from PIL import Image

class Store:
    _instance = None
    current_screen: Screen
    images: str
    _final_images: List[FinalImage]
    datetime: datetime
    latitude_deg: float
    latitude_ref: LatitudeRef
    longitude_deg: float
    longitude_ref: LongitudeRef
    address: str
    pic_name: str
    
    def __init__(self):
        self.current_screen = Screen.HOME
        self.images = None
        self._final_images = []
        self.datetime = None
        self.latitude_deg = None
        self.latitude_ref = None
        self.longitude_deg = None
        self.longitude_ref = None
        self.address = None
        self.pic_name = None
    
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
            }
        }
        
    def insert_final_image(self, image_path: str, image: Image.Image, exif_bytes: bytes):
        self._final_images.append(FinalImage(image_path=image_path, image=image, exif_bytes=exif_bytes))
        
    def get_final_images(self):
        return self._final_images

    def __repr__(self):
        return self.get_dict()
    
    def reset(self):
        self._instance = Store()