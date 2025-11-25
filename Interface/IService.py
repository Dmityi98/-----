from abc import abstractmethod, ABC

class IService(ABC):
    


    @abstractmethod
    def read_file(self, file_name):
        pass