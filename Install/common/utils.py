"""
The ``common.utils`` module contains function that are required by several
other modules within the ``common`` package.
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


def verifySqueeSAR():
    """
    This function verifies if the selected layer is a SqueeSAR layer, and if
    the data is available.

    Returns:
        layer (Layer): selected layer or data frame from the table of contents.

        md (MapDocument): reference to current map document.

    Raises:
        UserWarning: if an invalid layer is selected.
    """
    # Select current map
    # NOTE: To use the CURRENT keyword within a script tool, background
    # processing must be disabled. Background processing runs all scripts as
    # though they were being run as stand-alone scripts outside an ArcGIS
    # application, and for this reason, CURRENT will not work with background
    # processing enabled. There is a new script tool option called Always run
    # in foreground that ensures that a script tool will run in the foreground
    # even if background processing is enabled.
    md = ap.mapping.MapDocument("CURRENT")

    layer = pa.GetSelectedTOCLayerOrDataFrame()

    # Check if a layer is selected
    if not layer:
        pa.MessageBox("Select the SqueeSAR layer from the table of content\n" +
                      "then select an area to evaluate the residual",
                      "Warning",
                      0)

        raise UserWarning("Invalid layer!")

    # TODO: More tests should be added to verify if:
    #         - the selected layer is an squeesar layer
    return (layer, md)


def selectSqueeSARData(extent, layer):
    """
    This function translates the extent selected by the user into the spatial
    reference of the SqueeSAR layer and identifies the features within the
    selected area.

    Args:
        extent (Extent): the extent object identifying the user-selected area.

        layer (Layer): a reference to the layer containing the SqueeSAR data.

    Returns:
        nfeat (int): the number of features (scatterers) within the selected area.

        spatref (SpatialReference): the spatial reference of the SqueeSAR layer.

    Raises:
        UserWarning: if there is no data within the selection.

    """
    # Get the spatial reference of the SqueeSAR layer
    spatref = ap.Describe(layer).spatialReference

    # Convert the rectangle extent to a polygon
    area = ap.Array()  # Create empty array
    area.add(extent.lowerLeft)
    area.add(extent.lowerRight)
    area.add(extent.upperRight)
    area.add(extent.upperLeft)
    area.add(extent.lowerLeft)
    poly = ap.Polygon(area, spatref)

    # Select the data
    ap.SelectLayerByLocation_management(layer, "WITHIN", poly, 0.0, "NEW_SELECTION")

    # Evaluate the number of selected features
    nfeat = ap.GetCount_management(layer).getOutput(0)

    if nfeat == "0":
        pa.MessageBox("No features were available within the selection boundaries",
                      "Warning",
                      0)

        raise UserWarning("No features!")

    print("{0} feature(s) selected within:\n".format(nfeat) +
          "Lat: {0} to {1}\n".format(extent.YMin, extent.YMax) +
          "Lon: {0} to {1}\n".format(extent.XMin, extent.XMax))

    return (int(float(nfeat)), spatref)
