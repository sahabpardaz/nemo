import os
from apps.utils import scenario_utils


__location__ = os.path.dirname(__file__)
data_dir = os.path.join(__location__, "data")

def add_json_file_instances(file_path: str, serializer_class: scenario_utils.SerializerClass) -> scenario_utils.AddedInstancesType:
    return scenario_utils.add_json_file_instances(
        file_path=os.path.join(data_dir, file_path),
        serializer_class=serializer_class
    )
