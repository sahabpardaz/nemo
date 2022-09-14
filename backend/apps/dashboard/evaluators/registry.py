from typing import List

evaluator_registry = {}


def register(evaluation_kinds: List[str]):
    """
        Simple class decorator to register evalutor classes
        with supported evaluation kinds of them in registry.
    """
    def decorator(klass):
        for evaluation_kind in evaluation_kinds:
            if evaluator_registry.get(evaluation_kind) == klass:
                raise Exception(
                    f"More than one evaluator assigend to evaluation kind {evaluation_kind}."
                    f"When trying to add evaluator {klass} to registry, "
                    f"evaluator {evaluator_registry.get(evaluation_kind)} already registerd with this evaluation kind."
                )

            evaluator_registry[evaluation_kind] = klass

        return klass
    return decorator
