import argparse
import glob
import os
import sys
import tarfile


def main():

    # Unzip and untar granules
    input_dir = "input"
    granule_paths = glob.glob(os.path.join(input_dir, "*.tar.gz"))
    for g in granule_paths:
        tar_file = tarfile.open(g)
        tar_file.extractall(input_dir)
        tar_file.close()
        #os.remove(g)

    dirs = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    instrument = "PRISMA" if dirs[0][:3] == "PRS" else "AVIRIS"

    # Get paths based on product type file matching
    paths = []

    if instrument == "PRISMA":
        paths+= glob.glob(os.path.join(input_dir, "*", "*rfl_prj"))

    elif instrument == "AVIRIS":
        paths+= glob.glob(os.path.join(input_dir, "*rdn*", "*rdn*img"))
        paths+= glob.glob(os.path.join(input_dir, "*rdn*", "*obs_ort"))
        paths+= glob.glob(os.path.join(input_dir, "*rdn*", "*loc"))
        paths+= glob.glob(os.path.join(input_dir, "*rfl*", "*rfl"))

    for path in paths:
        print(path)

if __name__ == "__main__":
    main()
