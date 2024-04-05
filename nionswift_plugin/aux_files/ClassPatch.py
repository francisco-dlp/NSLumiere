import dataclasses
import typing
import gettext
import copy

from nion.instrumentation.stem_controller import ScanSpecifier, ScanContext
from nion.utils import Geometry
from nion.instrumentation import scan_base

_ = gettext.gettext

"""
calculate_time_size in ScanAcquisition is called by __update_estimate, responsible for updating the value seen by Nionswift in the spectrum imaging

> acquire_sequence inside ScanAcquisition launches the spectrum imaging
"""

def update(self, scan_hardware_source: scan_base.ScanHardwareSource, exposure_ms: float, scan_width: int, scan_count: int, drift_correction_enabled: bool) -> None:
    scan_context = scan_hardware_source.scan_context
    scan_context_size = scan_context.size
    if scan_context.is_valid and scan_hardware_source.line_scan_enabled and scan_hardware_source.line_scan_vector:
        assert scan_context_size
        calibration = scan_context.calibration
        start = Geometry.FloatPoint.make(scan_hardware_source.line_scan_vector[0])
        end = Geometry.FloatPoint.make(scan_hardware_source.line_scan_vector[1])
        length = int(Geometry.distance(start, end) * scan_context_size.height)
        max_dim = max(scan_context_size.width, scan_context_size.height)
        length_str = calibration.convert_to_calibrated_size_str(length, value_range=(0, max_dim), samples=max_dim)
        line_str = _("Line Scan")
        self.roi_description = f"{line_str} {length_str} ({length} px)"
        self.context_description = f"{line_str} {length_str}"
        scan_str = _("Scan (1D)")
        scan_length = max(scan_width, 1)
        drift_scans = scan_hardware_source.calculate_drift_scans()
        drift_str = f" / Drift every {drift_scans} scans" if drift_scans > 0 else str()
        self.scan_description = f"{scan_str} {scan_length} px" + drift_str
        self.__scan_pixels = scan_length
        self.scan_context = copy.deepcopy(scan_context)
        self.scan_context_valid = True
        self.scan_count = max(scan_count, 1)
        self.size = 1, scan_length
        self.scan_size = Geometry.IntSize(height=1, width=scan_length)
        self.scan_pixel_count = 1 * scan_length
        self.drift_interval_lines = 0
        self.drift_interval_scans = drift_scans
        self.drift_correction_enabled = drift_correction_enabled
    elif scan_context.is_valid and scan_hardware_source.subscan_enabled and scan_hardware_source.subscan_region:
        assert scan_context_size
        calibration = scan_context.calibration
        width = scan_hardware_source.subscan_region.width * scan_context_size.width
        height = scan_hardware_source.subscan_region.height * scan_context_size.height
        width_str = calibration.convert_to_calibrated_size_str(width, value_range=(0, scan_context_size.width), samples=scan_context_size.width)
        height_str = calibration.convert_to_calibrated_size_str(height, value_range=(0, scan_context_size.height), samples=scan_context_size.height)
        rect_str = _("Subscan")
        self.roi_description = f"{rect_str} {width_str} x {height_str} ({int(width)} px x {int(height)} px)"
        self.context_description = f"{rect_str} {width_str} x {height_str}"
        scan_str = _("Scan (2D)")
        scan_width = scan_width
        scan_height = int(scan_width * height / width)
        drift_lines = scan_hardware_source.calculate_drift_lines(scan_width, exposure_ms / 1000) if scan_hardware_source else 0
        drift_str = f" / Drift every {drift_lines} lines" if drift_lines > 0 else str()
        drift_scans = scan_hardware_source.calculate_drift_scans()
        drift_str = f" / Drift every {drift_scans} scans" if drift_scans > 0 else drift_str
        self.scan_description = f"{scan_str} {scan_width} x {scan_height} px" + drift_str
        self.__scan_pixels = scan_width * scan_height
        self.scan_context = copy.deepcopy(scan_context)
        self.scan_context_valid = True
        self.scan_count = max(scan_count, 1)
        self.size = scan_height, scan_width
        self.scan_size = Geometry.IntSize(height=scan_height, width=scan_width)
        self.scan_pixel_count = scan_height * scan_width
        self.drift_interval_lines = drift_lines
        self.drift_interval_scans = drift_scans
        self.drift_correction_enabled = drift_correction_enabled
    elif scan_context.is_valid:
        assert scan_context_size
        calibration = scan_context.calibration
        width = scan_context_size.width
        height = scan_context_size.height
        width_str = calibration.convert_to_calibrated_size_str(width, value_range=(0, scan_context_size.width), samples=scan_context_size.width)
        height_str = calibration.convert_to_calibrated_size_str(height, value_range=(0, scan_context_size.height), samples=scan_context_size.height)
        data_str = _("Context Scan")
        self.roi_description = f"{data_str} {width_str} x {height_str} ({int(width)} x {int(height)})"
        self.context_description = f"{data_str} {width_str} x {height_str}"
        scan_str = _("Scan (2D)")
        scan_width = scan_width
        scan_height = int(scan_width * height / width)
        drift_lines = scan_hardware_source.calculate_drift_lines(scan_width, exposure_ms / 1000) if scan_hardware_source else 0
        drift_str = f" / Drift every {drift_lines} lines" if drift_lines > 0 else str()
        drift_scans = scan_hardware_source.calculate_drift_scans()
        drift_str = f" / Drift every {drift_scans} scans" if drift_scans > 0 else drift_str
        self.scan_description = f"{scan_str} {scan_width} x {scan_height} px" + drift_str
        self.__scan_pixels = scan_width * scan_height
        self.scan_context = copy.deepcopy(scan_context)
        self.scan_context_valid = True
        self.scan_count = max(scan_count, 1)
        self.size = scan_height, scan_width
        self.scan_size = Geometry.IntSize(height=scan_height, width=scan_width)
        self.scan_pixel_count = scan_height * scan_width
        self.drift_interval_lines = drift_lines
        self.drift_interval_scans = drift_scans
        self.drift_correction_enabled = drift_correction_enabled
    else:
        self.clear()

ScanSpecifier.update = update