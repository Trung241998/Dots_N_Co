"""Utility functions/classes for CSSE1001 Assignment 3, Semester 2, 2017"""

__author__ = "Benjamin Martin"
__copyright__ = "Copyright 2017, The University of Queensland"
__license__ = "MIT"
__version__ = "1.1.1"


def create_animation(widget, generator, delay=200, delays=None, step=None, callback=None):
    """Creates a function which loops through a generator using the tkinter
    after method to allow for animations to occur

    Parameters:
        widget (tk.Widget): A tkinter widget (that has a .after method)
        generator (generator): The generator yielding animation steps
        delay (int): The default delay (in milliseconds) between steps
        delays (dict<str, int>): A map of specific delays for specific types of steps 
        step (callable): The function to call after each step
                         Accepts (step_type:str) as only argument
        callback (callable): The function to call after all steps

    Return:
        (callable): The animation runner function
    """

    def runner():
        """Runs animation"""
        try:
            step_type = next(generator)
            widget.after(delays.get(step_type, delay), runner)
            if step is not None:
                step(step_type)
        except StopIteration:
            if callback is not None:
                callback()

    return runner


class ImageManager:
    """Simple image manager to load images with simple caching"""
    def __init__(self, *args, loader=lambda image_id, size, *args: None):
        """Constructor
        
        Parameters:
            args (*): Extra arguments to pass to the loader (see below)
            loader (callable<filepath (str)>): Callable that returns loaded image object
                                               filepath parameter corresponds to image to be loaded
        """
        self.reset()
        self._args = args
        self._loader = loader

    def load(self, image_id, size):
        """Loads an image
        
        Parameters:
            image_id (str): The id of the image to load
            
        Return:
            *: Whatever the loader callable passed to the constructor returns
        """

        key = (size, image_id)

        if key not in self._images:
            self._images[key] = self._loader(image_id, size, *self._args)

        return self._images[key]

    def reset(self):
        """Resets the image manager"""
        self._images = {}
