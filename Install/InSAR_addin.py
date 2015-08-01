"""
This is the main entry point for the InSAR Add-In.

For each tool defined in the ``config.xml`` file, there is a corresponding
class in this file and, for each class, the enabled method.

Things to keep in mind:

- This add-in is not a standalone application but it is supposed to be run from
  within the ArcMAP environment. As such it assumes the availability of the
  ``arcpy`` package and the ``pythonaddins`` modules which are part of the
  ArcGIS distribution.
- The initialization of each class occurs when arcmap starts and the addin is
  loaded.
- The code assumes that only homogenous data is selected and that the fields
  correspond to the one used by TRE in their data.
- At start time, ArcMAP instantiates an object for each of the classes using a
  name corresponding to the ID specified in the ``config.xml`` file. This
  requires extra caution when defining the name of modules since a duplication
  of the name will cause the add-in to mulfunction at runtime. Furthermore, the
  name is only defined in the ``config.xml`` file hence not visible from within
  the development environment. Extra care should be placed in naming packages
  and modules.
- Because of the above point, the ``__init__`` method of each class defined for
  each tool in the ``config.xml`` file is run at program start up.

.. note::
   TODOs:

   - Since the add-in is run *in process*, we might want to move the
     functionality into toolbox/tools, import them when the add-in is
     initialized, and then call the tools from within the plugin. This would
     also allow the user to enter parameters.
   - Would be nice to use an extension to only enable the toolbar if a SqueeSAR
     layer is available. How do we determine if one is indeed available? How do
     we keep looking if a layer is added? ``itemAdded(self, new_item)`` method
     in the extension?
   - The checking could be extended to allow individual tools depending on the
     environment conditions.
   - There should be more trapping of potential errors with the ``try``
     construct
   - If any error occurs whie loading the add-in during startup, the entire
     ArcMAP will crash and will not start. This *HAS* to be fixed.

.. caution::
   The add-ins run *in process*. Since the evaluation takes a long time, ArcMAP
   will be locked for the duration of the processing. The algorithm should be
   moved to a toolbox and then called from the addin. Toolboxes can run in
   background!
"""

# For debugging purposes only. It will lock ArcGIS for 5 minutes if winpdb is
# not available.
#import rpdb2
#rpdb2.start_embedded_debugger('123')

# Let python know there are more modules in this directory
import os
import sys
sys.path.append(os.path.dirname(__file__))

# Try to import *arcpy* (provided by ArcGIS)
try:
    import arcpy as ap
except ImportError as e:
    print(e.message)
    raise

# Try to import *pythonaddins* (provided by ArcGIS)
try:
    import pythonaddins as pa
except ImportError as e:
    print(e.message)
    raise

# Try to import *numpy* (should be provided by ArcGIS as well)
try:
    import numpy as np
except ImportError as e:
    pa.MessageBox(e.message, "Error")
    raise

# Try to import the rest of the add-in
try:
    from common import utils
except ImportError as e:
    pa.MessageBox(e.message, "Error", 0)
    raise

try:
    from common import avevel
except ImportError as e:
    pa.MessageBox(e.message, "Error", 0)
    raise

try:
    from common import subres
except ImportError as e:
    pa.MessageBox(e.message, "Error", 0)
    raise

# Few globals about the addin
PROJECT = u"InSAR Add-in"
NAME = u"InSAR Analysis Add-in"
AUTHOR = u"Andrea Vaccari (viva.uva@gmail.com)"
COMPANY = u"University of Virginia Image and Video Analysis Laboratory (VIVA)"
VERSION = u"0.0"
RELEASE = u"[0.0.2alpha]"
YEAR = u"2014"



class AboutButton(object):
    """
    The class ``AboutButton`` is the implementation for the *about*
    button.
    """
    def __init__(self):
        """
        The ``__init__()`` method is called when ArcMAP starts up, right
        after loading the add-in. This method performs simple initialization
        such as setting the ``enabled`` status of the button to ``True`` and
        unchecking it.
        """
        self.enabled = True
        self.checked = False

    def onClick(self):
        """
        The ``onClick()`` method is called when the button is clicked.

        This method displays a pop-up windows including information about the
        add-in.
        """
        self.checked = True
        pa.MessageBox(NAME + " (Release: " + RELEASE + ")\n" +
                      "Developed by " + AUTHOR + "\n" +
                      COMPANY,
                      "About",
                      0)
        self.checked = False



# Implementation for the average displacement velocity tool
class AverageDisplacementVelocity(object):
    """
    The class ``AverageDisplacementVelocity`` is the implementation of the
    *average displacement velocity* tool.
    """
    def __init__(self):
        """
        The ``__init__()`` method is called when ArcMAP starts up, right
        after loading the add-in.This method performs simple initialization
        such as setting the ``enabled`` status of the tool to ``True`, defining
        the type of shape used to select the area of interest (*rectangle*),
        changing the cursor to crosshair, and initializing other global
        parameters required by the implementation.
        """
        self.enabled = True
        self.shape = "Rectangle"  # Define drawing shape and activate the event sinks.
        self.cursor = 3  # Change to a crosshair cursor
        self.sar = None  # Layer with SqueeSAR data
        ap.env.addOutputsToMap = False  # Disable automatic autput to map
        ap.env.overwriteOutput = True  # Overwrite datasets
        #ap.ImportToolbox(os.path.join(os.path.dirname(os.path.realpath(__file__)), "toolbox\\InSAR_tbox.pyt"))  # Import toolbox


    def deactivate(self):
        """
        The ``deactivate()`` method is called when ArcGIS deactivates the tool.
        It cannot be called programmatically. This is where cleanup should
        happen.  In this particular case, the user selection is cleared.
        """
        if self.sar:
            ap.SelectLayerByAttribute_management(self.sar, "CLEAR_SELECTION")

    def onRectangle(self, rectangle_geometry):
        """
        The ``onRectangle()`` method is called after the user has activated the
        tool and selected an area of interest. This is where the main part of
        the tool is executed.

        This method calls the :func:`common.avevel.evaluate` function where the
        average displacement velocity is computed.

        After popping-up a window with the result, the selection is cleared and
        the method returns.

        Args:
            rectangle_geometry (Extent): the extent of the selection.
                This argument is passed directly by the ArcMAP enviromnment
                upon execution of the add-in.
        """
        # Detect if a layer is selected
        try:
            self.sar, md = utils.verifySqueeSAR()
        except "Invalid layer!":
            return

        # Identiy user selected data
        try:
            nfeat, spatref = utils.selectSqueeSARData(rectangle_geometry, self.sar)
        except "No features!":
            return

        # Evaluate average velocity
        ave_vel = avevel.evaluate(self.sar)

        # Pop-up a message box with the informations
        text = "{0} feature(s) selected within:\n".format(nfeat) + \
               "Lat: {0} to {1}\n".format(rectangle_geometry.YMin, rectangle_geometry.YMax) + \
               "Lon: {0} to {1}\n\n".format(rectangle_geometry.XMin, rectangle_geometry.XMax) + \
               "Average velocity: {:.2f} mm/year".format(ave_vel)

        pa.MessageBox(text,
                      "Info",
                      0)

        # Clear selection
        ap.SelectLayerByAttribute_management(self.sar, "CLEAR_SELECTION")












class SubsidenceResidual(object):
    """
    The class ``SubsidenceResidual`` is the implementation of the *subsidence
    residual* tool.
    """
    def __init__(self):
        """
        The ``__init__()`` method is called when ArcMAP starts up, right
        after loading the add-in.This method performs simple initialization
        such as setting the ``enabled`` status of the tool to ``True`, defining
        the type of shape used to select the area of interest (*rectangle*),
        changing the cursor to crosshair, and initializing other global
        parameters required by the implementation.
        """
        self.enabled = True
        self.shape = "Rectangle"  # Define drawing shape and activate the event sinks.
        self.cursor = 3  # Change to a crosshair cursor
        self.sar = None  # Layer with SqueeSAR data
        ap.env.addOutputsToMap = False  # Disable automatic autput to map
        ap.env.overwriteOutput = True  # Overwrite datasets
#        ap.ImportToolbox(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Toolbox\\InSAR_tbox.pyt"))  # Import toolbox


    def deactivate(self):
        """
        The ``deactivate()`` method is called when ArcGIS deactivates the tool.
        It cannot be called programmatically. This is where cleanup should
        happen. In this particular case, the user selection is cleared.
        """
        if self.sar:
            ap.SelectLayerByAttribute_management(self.sar, "CLEAR_SELECTION")

    def onRectangle(self, rectangle_geometry):
        """
        The ``onRectangle()`` method is called after the user has activated the
        tool and selected an area of interest. This is where the main part of
        the tool is executed.

        In order for the evaluation to be carried on, there should be *at least
        3 scatterers* selected.

        This method calls the :func:`common.subres.evaluate` function where the
        subsidence residual map is computed.

        The result of the residual evaluation is stored in a raster file (named
        *subsidence*) within the default geodatabase. The raster is also added
        as a layer (with the same name) and overlayed with transparency over
        the area selected by the user.

        Args:
            rectangle_geometry (Extent): the extent of the selection.
                This argument is passed directly by the ArcMAP enviromnment
                upon execution of the add-in.
        """
        # Detect if a layer is selected
        try:
            self.sar, md = utils.verifySqueeSAR()
        except "Invalid layer!":
            return

        # TODO: At this point the parameters of the Gaussian search space should be known.
        #       We should extend the underlying selection to include 3 sigma extra to allow for full analysis
        #       The variable extent should be modified to include the additional area
        extent = rectangle_geometry

        # Identiy user selected data
        try:
            nfeat, spatref = utils.selectSqueeSARData(extent, self.sar)
        except "No features!":
            return

        # Verify that the number of selected scatterers is larger than three
        if nfeat < 3:
            pa.MessageBox("At least 3 features required within the selection boundaries",
                          "Warning",
                          0)
            return

        # Evaluate residual raster
        res = subres.evaluate(extent, self.sar)

        # Evaluate the size of the raster cell
        (x_len, y_len) = np.shape(res)
        x_cell_size = extent.width / x_len
        y_cell_size = extent.height / y_len

        # Define the spatial coordinate system using the spatial reference
        # obtained from the selected SqueeSAR layer.
        ap.env.outputCoordinateSystem = spatref

        # Convert the returned numpy array into a raster file and store it
        raster = ap.NumPyArrayToRaster(res, extent.lowerLeft, x_cell_size, y_cell_size)
        raster.save("subsidence")

        # Select the first dataframe and create a raster layer
        df = ap.mapping.ListDataFrames(md)[0]
        add_layer = ap.mapping.Layer("subsidence")

        # If transparency is supported, set to 25%
        if add_layer.supports("TRANSPARENCY"):
            add_layer.transparency = 25

        # Add the raster layer to the top
        ap.mapping.AddLayer(df, add_layer, "TOP")

        # Clear the current selection
        ap.SelectLayerByAttribute_management(self.sar, "CLEAR_SELECTION")





