class Store:
    _instance = None
    current_screen = "home"
    images = None
    final_images = None
    datetime = None
    latitude_deg = None
    latitude_ref = None
    longitude_deg = None
    longitude_ref = None
    address = None
    
    def __new__(self, *args, **kwargs):
        if not self._instance:
            self._instance = super(Store, self).__new__(self, *args, **kwargs)
        return self._instance

    def get_dict(self):
        return {
            "images": self.images,
            "finalImages": self.final_images,
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

    def __repr__(self):
        return self.get_dict()
    
    def reset(self):
        self._instance = Store()