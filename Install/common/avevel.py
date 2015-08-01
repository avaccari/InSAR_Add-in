"""
This module implments the code necessary to evauate the average displacement
velocity of a group of SqueeSAR scatterers selected by the user.
"""

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
    pa.MessageBox(e.message, "Error", 0)
    raise


def evaluate(layer):
    """
    This function evaluates the actual average displacement velocity.

    Args:
        layer (Layer): a reference to the layer containing the SqueeSAR data.

    Returns:
        ave_vel (float): the average displacement velocity of the selected scatterers.
    """
    # Extract field names from the layer
    fld = ap.ListFields(layer)
    fld_names = [f.name for f in fld]

    # Store all data in a structured array
    sel_data = ap.da.FeatureClassToNumPyArray(layer, fld_names)

    # Calculate average displacement velocity. The displacment velocity is
    # "usually" stored in the u"VEL" field.
    if u"VEL" not in fld_names:
        pa.MessageBox("Couldn't find the field 'VEL' in the data.",
                      "Error",
                      0)
    ave_vel = np.average(sel_data[u"VEL"])
    # TODO: I don't really like using named variable. Is there a way to find out or ask the user?

    return ave_vel
