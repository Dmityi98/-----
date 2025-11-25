from abc import abstractmethod, ABC

class IModel(ABC):

    @abstractmethod
    def answer(self,registration_text, text_order):
        pass