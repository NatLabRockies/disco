import os
import glob
import sys
import pathlib


def get_paths(root, filename):
    """"Finds all paths to filename from a root path in 4.8kV feeders"""
    return [y for x in os.walk(root) for y in glob.glob(os.path.join(x[0], filename)) 
            if os.path.basename(os.path.dirname(y))[0].isdigit()]


def create_paths(root_path, filename, text_file_path):
    print(f"Identifying filepaths for this scenario...")
    master_files = get_paths(root_path, filename)
    print(f"Paths identified!")
    write_text_file(master_files, text_file_path=text_file_path, num_new_lines=2)
    return
    
def write_text_file(string_list, text_file_path, num_new_lines=2):
    """This function writes the string contents of a list to a text file

    Parameters
    ----------
    string_list
    text_file_path

    Returns
    -------

    """
    breaks = "\n"*num_new_lines
    pathlib.Path(text_file_path).write_text(breaks.join(string_list))


if __name__ =="__main__":

    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]}")
        # print(f"Usage: python {sys.argv[0]} LOAD_SCENARIO <moderate> YEAR <2045> ")
        # f"PATH_TO_PARENT_FOLDER </projects/la100/run2/distribution/sim/c0/>")
        sys.exit(1)
        
    # territory_path = "/lustre/eaglefs/projects/la100/run2/dist/c1_7/feeder_models/opendss/moderate/2020/2012-08-11_19-00-00-000"
    

    # load_scenario = sys.argv[1]
    # year = sys.argv[2]

    load_scenario = 'moderate'
    year = '2020'

    cycle = "c1_7"
    date = "2012-08-11_19-00-00-000"

    # actual root path to be used
    root_path = f"/lustre/eaglefs/projects/la100/run2/dist/{cycle}/feeder_models/opendss/{load_scenario}/{year}/{date}"
    print(f"\n\n*********LOAD SCENARIO:{load_scenario}, YEAR: {year}, DATE: {date}*************")
    if os.path.exists(root_path):
        print(f'{root_path} exists!')
    else:
        raise Exception(f"{root_path} does not exist!")
    filename = "Master.dss"
    
    output_path = "/scratch/sabraham/la100es"
    create_paths(root_path, filename=filename, text_file_path=os.path.join(output_path, f"sep_{year}_{load_scenario}_feeders.txt"))
    
    
    