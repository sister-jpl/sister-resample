#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Adam Chlus
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import hytools_lite as ht
from hytools_lite.io.envi import WriteENVI
import numpy as np

def main():
    '''
    Project location file using the geometry lookup table (GLT).

    This function takes a single argurment, the pathname to the location file, and
    assumes the GLT and LOC image are located in the same folder and use the same
    file naming convention.

    The projected location file is written to the same directory as the
    input file.

    '''

    loc_file =sys.argv[1]
    loc = ht.HyTools()
    loc.read_file(loc_file,'envi')

    glt_file =  loc_file.replace('loc','glt')
    glt = ht.HyTools()
    glt.read_file(glt_file,'envi')

    samples = np.abs(glt.get_band(0))
    lines = np.abs(glt.get_band(1))

    lon = np.copy(loc.get_band(0))
    lat= np.copy(loc.get_band(1))
    elv = np.copy(loc.get_band(2))

    lon_proj = lon[lines.flatten()-1,samples.flatten()-1]
    lon_proj = lon_proj.reshape(lines.shape)

    lat_proj = lat[lines.flatten()-1,samples.flatten()-1]
    lat_proj = lat_proj.reshape(lines.shape)

    elv_proj = elv[lines.flatten()-1,samples.flatten()-1]
    elv_proj = elv_proj.reshape(lines.shape)

    lon_proj[samples ==0] = -9999
    lat_proj[samples ==0] = -9999
    elv_proj[samples ==0] = -9999

    # Create output file
    output_file = loc.file_name+'_ort'
    header_dict =glt.get_header()
    header_dict['bands'] = 3
    header_dict['data type'] = 4
    header_dict['band names'] = loc.get_header()['band names']
    header_dict['description'] = loc.get_header()['description']
    writer = WriteENVI(output_file,header_dict)
    writer.write_band(lon_proj,0)
    writer.write_band(lat_proj,1)
    writer.write_band(elv_proj,2)

if __name__ == "__main__":
    main()
