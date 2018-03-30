# Standard library imports
import functools

# Local imports
from uplink import converters, decorators, utils

__all__ = ["load", "dump"]

_get_classes = functools.partial(map, type)


class _ModelConverterBuilder(object):

    def __init__(self, base_class, annotations=()):
        """
        Args:
            base_class (type): The base model class.
        """
        self._model_class = base_class
        self._annotations = set(annotations)
        self._func = None

    def using(self, func, _r=converters.register_default_converter_factory):
        self._func = func
        _r(self)
        return func

    __call__ = using

    def _contains_annotations(self, argument_annotations, method_annotations):
        types = set(_get_classes(argument_annotations))
        types.update(_get_classes(method_annotations))
        return types.issuperset(self._annotations)

    def _is_relevant(self, type_, argument_annotations, method_annotations):
        return (
            utils.is_subclass(type_, self._model_class) and
            self._contains_annotations(argument_annotations, method_annotations)
        )

    def _marshall(self, type_, *args, **kwargs):
        if self._is_relevant(type_, *args, **kwargs):
            return functools.partial(self._func, type_)


class load(_ModelConverterBuilder, converters.ConverterFactory):
    """
    Builds a custom object deserializer.

    This decorator takes a single argument, the base model class, and
    registers the decorated function as a deserializer for that base
    class and all subclasses.

    Further, the decorated function should accept two positional
    arguments: (1) the encountered type (which can be the given base
    class or a subclass), and (2) the response data.

    .. code-block:: python

        @models.load(ModelBase)
        def load_model(model_cls, data):
            ...
    """

    def make_response_body_converter(self, *args, **kwargs):
        return self._marshall(*args, **kwargs)


load.from_json = functools.partial(load, annotations=(decorators.returns.json,))
"""
Builds a custom JSON deserialization strategy.

This decorator accepts the same arguments and behaves like
:py:class:`uplink.models.load`, except that the second argument of the
decorated function is always a JSON object:

.. code-block:: python

    @models.load.from_json(ModelBase)
    def from_json(model_cls, json_object):
        return model_cls.from_json(json_object)

Notably, only consumer methods that have the expected return type (i.e.,
the given base class or any subclass) and are decorated with
:py:class:`uplink.returns.json` can leverage the registered strategy to
deserialize JSON responses.

For example, the following consumer method would leverage the
:py:func:`from_json` strategy defined above, only if :py:class:`User` is
a subclass of :py:class:`ModelBase`:

.. code-block:: python
    
    @returns.json
    @get("user")
    def get_user(self) -> User: pass
"""


class dump(_ModelConverterBuilder, converters.ConverterFactory):
    """
    Builds a custom object serializer.

    This decorator takes a single argument, the base model class, and
    registers the decorated function as a serializer for that base
    class and all subclasses.

    Further, the decorated function should accept two positional
    arguments: (1) the encountered type (which can be the given base
    class or a subclass), and (2) the encountered instance.

    .. code-block:: python

        @models.dump(ModelBase)
        def deserialize_model(model_cls, model_instance):
            ...
    """

    def make_request_body_converter(self, *args, **kwargs):
        return self._marshall(*args, **kwargs)


dump.to_json = functools.partial(dump, annotations=(decorators.json,))
"""
Builds a custom JSON serialization strategy.

This decorator accepts the same arguments and behaves like
:py:class:`uplink.models.dump`. The only distinction is that the
decorated function should return a JSON object.

.. code-block:: python

    @models.dump.to_json(ModelBase)
    def to_json(model_cls, model_instance):
        return model_instance.to_json()

Notably, only consumer methods that are decorated with
py:class:`uplink.json` and have one or more argument annotations with
the expected type (i.e., the given base class or a subclass) can
leverage the registered strategy.

For example, the following consumer method would leverage the
:py:func:`to_json` strategy defined above, only if :py:class:`User` is a
subclass of :py:class:`ModelBase`:

.. code-block:: python
    
    @json
    @post("user")
    def change_user_name(self, name: Field(type=User): pass
"""
