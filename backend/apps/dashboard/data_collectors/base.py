from abc import abstractmethod, ABC


class DataCollector(ABC):
    @abstractmethod
    def collect_and_save_data(self):
        pass
