from rest_framework import serializers


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    https://www.django-rest-framework.org/api-guide/serializers/#dynamically-modifying-fields
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


def set_one_to_many_composition(parent_instance, child_list_data, child_serializer, parent_name: str, children_name: str) -> None:
    """
    Sets the association values in a composition relationship and creaetes the child instances.
    """
    for child_data in child_list_data:
        child_data[parent_name] = parent_instance
    children = child_serializer.create(child_list_data)
    getattr(parent_instance, children_name).set(children)


def set_one_to_one_reverse_composition(parent_instance, child_data, child_serializer, parent_name: str, child_name: str) -> None:
    """
    Sets the association value in a composition relationship and creaetes the child instance.
    Assumption: the child has a OneToOneField to the parent.
    """
    if child_data is None:
        return
    child_data[parent_name] = parent_instance
    child = child_serializer.create(child_data)
    setattr(parent_instance, child_name, child)
