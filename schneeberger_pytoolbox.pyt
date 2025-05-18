# -*- coding: utf-8 -*-

import arcpy
import os


class Toolbox:
    def __init__(self):
        self.label = "Hydrological Analysis Toolbox"
        self.alias = "hydro_toolbox"

        # the list of tools associated with this toolbox
        self.tools = [BulkHydroAnalysis, OptimizedWatershed]


class BulkHydroAnalysis:
    def __init__(self):
        self.label = "Bulk Hydro Analysis"
        self.description = "This tool takes a single DEM as an input and automatically calculates basic hydrological outputs with optimized parameters"

    def getParameterInfo(self):
        # fetching parameters from the ArcGIS Pro geoprocessing GUI
        input_dem = arcpy.Parameter(
            displayName="Input DEM",
            name="input_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        output_workspace = arcpy.Parameter(
            displayName="Output Workspace (Folder or GDB)",
            name="output_workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )

        add_data_to_map = arcpy.Parameter(
            displayName="Automatically add Layers to Map",
            name="add_data_to_map",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )

        params = [input_dem, output_workspace, add_data_to_map]
        return params

    def isLicensed(self):
        # checking if the user has the requiered extensions for using this tool
        try:
            if arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception as e:
            arcpy.AddError(
                f"This tool requieres the Spatial Analyst extension: {e}")
            return False

        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # source (executing) code of the tool

        # reading parameters inputed by the user
        in_dem = parameters[0].valueAsText
        output_workspace = parameters[1].valueAsText
        add_data_to_map = parameters[2].valueAsText

        # Get the current project's active map for later reference
        project = arcpy.mp.ArcGISProject("CURRENT")
        active_map = project.activeMap

        # Check workspace type (folder or GDB) inputed by the user
        workspace_type = arcpy.Describe(output_workspace).workspaceType
        is_file_system = workspace_type == "FileSystem"

        # Helper function to construct output paths based on workspace type
        def construct_path(base_name):
            return os.path.join(output_workspace, f"{base_name}.tif") if is_file_system else os.path.join(output_workspace, base_name)

        # Defining output paths
        output_paths = {
            "sink_raster": construct_path("sink_raster"),
            "filled_dem": construct_path("filled_dem"),
            "flowdir_raster": construct_path("flowdir_raster"),
            "flowaccu_raster": construct_path("flowaccu_raster"),
            "stream_as_raster": construct_path("stream_as_raster"),
            "flow_distance_raster": construct_path("flow_distance_raster"),
            "flow_length_raster": construct_path("flow_length_raster"),
            "stream_link_raster": construct_path("stream_link_raster"),
            "stream_order_raster": construct_path("stream_order_raster")
        }

        # ANALYSIS
        # 1 Calculating Sink Raster
        sink_raster = arcpy.sa.Sink(arcpy.sa.FlowDirection(in_dem))
        sink_raster.save(output_paths["sink_raster"])

        # 2 Calculate Mean Sink Depth (to be used as Z-Limit for Fill tool)
        depth_raster = arcpy.sa.Minus(arcpy.sa.Fill(
            in_dem), arcpy.sa.Raster(in_dem))

        mean_depth = arcpy.sa.ZonalStatistics(
            sink_raster,
            "VALUE",
            depth_raster,
            "MEAN"
        )

        mean_depth_value = float(mean_depth.mean)

        # 2.5 Calculating filled DEM Raster based on Z-Limit in step #2
        filled_dem = arcpy.sa.Fill(in_dem, mean_depth_value)
        filled_dem.save(output_paths["filled_dem"])

        # 3 Calculating actual Flow Direction D8 Raster
        flowdir_D8_raster = arcpy.sa.FlowDirection(filled_dem)
        flowdir_D8_raster.save(output_paths["flowdir_raster"])

        # 4 Calculating Flow Accumulation Raster
        flowaccu_raster = arcpy.sa.FlowAccumulation(flowdir_D8_raster)
        flowaccu_raster.save(output_paths["flowaccu_raster"])

        # 5 Calculating Stream As Raster
        stream_as_raster = arcpy.sa.DeriveStreamAsRaster(in_dem)
        stream_as_raster.save(output_paths["stream_as_raster"])

        # 6 Calculating Flow Distance
        flow_distance_raster = arcpy.sa.FlowDistance(
            stream_as_raster, filled_dem, flowdir_D8_raster)
        flow_distance_raster.save(output_paths["flow_distance_raster"])

        # 7 Calculating Flow Length
        flow_length_raster = arcpy.sa.FlowLength(flowdir_D8_raster, "UPSTREAM")
        flow_length_raster.save(output_paths["flow_length_raster"])

        # 8 Calculating Stream Link
        stream_link_raster = arcpy.sa.StreamLink(
            stream_as_raster, flowdir_D8_raster)
        stream_link_raster.save(output_paths["stream_link_raster"])

        # 9 Calculating Stream Order
        stream_order_raster = arcpy.sa.StreamOrder(
            stream_as_raster, flowdir_D8_raster)
        stream_order_raster.save(output_paths["stream_order_raster"])

        # Add layers to the map if the user opted in
        if add_data_to_map:
            for path in output_paths.values():
                active_map.addDataFromPath(path)

        return

    def postExecute(self, parameters):
        return


class OptimizedWatershed:
    def __init__(self):
        self.label = "Optimized Watershed"
        self.description = "This Tool calculates a Watershed Raster based on optimized Pour Point locations"

    def getParameterInfo(self):
        # fetching parameters from the ArcGIS Pro geoprocessing GUI
        input_dem = arcpy.Parameter(
            displayName="Input DEM",
            name="input_dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        input_zlimit = arcpy.Parameter(
            displayName="Custom Z-limit for Fill Tool (optional)",
            name="input_zlimit",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
        )

        input_dem_resolution = arcpy.Parameter(
            displayName="Input DEM resolution",
            name="input_dem_resolution",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
        )

        input_pourpoint_raster = arcpy.Parameter(
            displayName="Input Raster for Pour Point Locations",
            name="input_pourpoint_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        watershed_raster_output_location = arcpy.Parameter(
            displayName="Watershed Raster Output Location",
            name="watershed_raster_output_location",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )

        add_data_to_map = arcpy.Parameter(
            displayName="Automatically add Layer to Map",
            name="add_data_to_map",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
        )

        params = [input_dem, input_zlimit, input_dem_resolution, input_pourpoint_raster,
                  watershed_raster_output_location, add_data_to_map]
        return params

    def isLicensed(self):
        # checking if the user has the requiered extensions for using this tool
        try:
            if arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception as e:
            arcpy.AddError(
                f"This tool requieres the Spatial Analyst extension: {e}")
            return False

        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        # enforcing a positive value if the user specifies his own z-limit
        input_zlimit = parameters[1].value

        if input_zlimit is not None and input_zlimit <= 0:
            parameters[5].setErrorMessage("Z-limit must be a positive number.")

        return

    def execute(self, parameters, messages):
        # source (executing) code of the tool

        # reading parameters inputed by the user
        in_dem = parameters[0].valueAsText
        input_zlimit = parameters[1].valueAsText
        in_dem_res = float(parameters[2].valueAsText)
        in_pp_raster = parameters[3].valueAsText
        ws_raster_output = parameters[4].valueAsText
        add_data_to_map = parameters[5].valueAsText

        # Get the current project's active map
        project = arcpy.mp.ArcGISProject("CURRENT")
        active_map = project.activeMap

        # Check workspace type of watershed raster output location (folder or GDB)
        ws_raster_outtype = arcpy.Describe(
            ws_raster_output).workspaceType
        ws_raster_out_is_file_system = ws_raster_outtype == "FileSystem"

        # Defining output paths
        ws_raster_output_path = None
        if ws_raster_out_is_file_system:
            ws_raster_output_path = os.path.join(
                ws_raster_output, "watershed_raster.tif")
        else:
            ws_raster_output_path = os.path.join(
                ws_raster_output, "watershed_raster")

        # ANALYSIS
        # DEM preprocessing - filling sinks based on user defined z-limit (if z-limit defined) or based on mean sink depth (if z-limit undefined)
        if input_zlimit:
            filled_dem = arcpy.sa.Fill(in_dem, float(input_zlimit))
        else:
            sink_raster = arcpy.sa.Sink(arcpy.sa.FlowDirection(in_dem))
            depth_raster = arcpy.sa.Minus(arcpy.sa.Fill(
                in_dem), arcpy.sa.Raster(in_dem))
            mean_depth = arcpy.sa.ZonalStatistics(
                sink_raster,
                "VALUE",
                depth_raster,
                "MEAN"
            )
            mean_depth_value = float(mean_depth.mean)
            filled_dem = arcpy.sa.Fill(in_dem, mean_depth_value)

        # Pre Calculations for using the Watershed Tool
        flowdir_D8_raster = arcpy.sa.FlowDirection(filled_dem)
        flow_acc_raster = arcpy.sa.FlowAccumulation(flowdir_D8_raster)

        # calculating a snaping distance for the SnapPourPoint Tool based on the input_dem cell size
        snap_distance = None
        if in_dem_res >= 10:
            snap_distance = in_dem_res * 10
        elif in_dem_res >= 2:
            snap_distance = in_dem_res * 7
        else:
            snap_distance = in_dem_res * 5

        # optimizing input Pour Point Raster to areas with the highest accumulated flow
        opti_pp_raster = arcpy.sa.SnapPourPoint(
            in_pp_raster, flow_acc_raster, snap_distance, "Value")

        # Watershed Calculation
        watershed_raster = arcpy.sa.Watershed(
            flowdir_D8_raster, opti_pp_raster, "Value")
        watershed_raster.save(ws_raster_output_path)

        # Add layer to the map if the user opted in
        if add_data_to_map:
            active_map.addDataFromPath(ws_raster_output_path)

        return

    def postExecute(self, parameters):
        return
