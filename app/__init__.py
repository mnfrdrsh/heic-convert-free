__all__ = ["ImageConverterApp"]


def __getattr__(name):
    if name == "ImageConverterApp":
        from .gui import ImageConverterApp

        return ImageConverterApp

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
