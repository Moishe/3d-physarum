This is an application that will build a 3D model based on the Physarum algorithm. It has these properties:

* The colony starts from a central "base" and can only grow upward. You can thus think of movement along the Z axis as movement through time in a 2D physarum simulation.
* The resulting model must be completely self-connected -- there can't be any pieces of it that are completely disconnected, when the Z axis is considered.
* The application runs on the command line, and emits a 3D rendering of the final product as a JPG, in addition to an .STL file suitable for 3D printing.
* While the simulation itself will need to use multiple values per pixel to indicate physarum decay, the finished model won't support colors.
* The command line application will take parameters to control standard physarum simulation parameters (number of actors, rate of decay, view radius and distance, etc)
