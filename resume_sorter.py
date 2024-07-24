import os
import json
from filename_mgr import FilenameManager

# "initialise" method:
# takes resumes from unranked folder and gives default (1500) rating

# create glicko2.Player() objects for each resume in the folder
# meaning there needs to be a `ratings.json` file
# stores {"<filename>": {"rating": 1500, "sd": 26}} etc

# okay suppose we have all the Player() objects we need...
# pick n unique pairings
# find winner and update rank

# FileManager
# reads from json file
# sends relevant info to RatingsManager

# RatingManager
# Constructs Player() objects
# sends new ratings to FileManager

class ResumeManager:
    """
    Manages resume files themselves. Includes keeping track of ratings,
    names of files, and which folder resume files should be in.
    """

    RATING_DEFAULT = 1500
    RD_DEFAULT = 350       # Rating Deviation (Uncertainty in rating)
    VOL_DEFAULT = 0.06     # Volatility (Expected change in rating)
    
    def __init__(self, resume_folder):
        self.resume_fol = resume_folder
        self.unranked_fol = f'./{self.resume_fol}/unranked'
        self.ranked_fol = f'./{self.resume_fol}/ranked'

        self.filename_mgr = FilenameManager()

    def init_unranked(self):
        self.init_unranked_into_json()
        self.init_unranked_into_ranked()

    def init_unranked_into_json(self):
        """Adds unranked resumes into `ratings.json`"""

        filepath = f'{self.resume_fol}/ratings.json'
        with open(filepath, 'r') as f:
            ratings_data = json.load(f)

        for filename in os.listdir(self.unranked_fol):
            if filename in ratings_data:
                print(f'File named "{filename}" is already initialised in ratings.json')
                print("Skipping...")
                continue

            ratings_data[filename] = {"rating": self.RATING_DEFAULT,
                                          "rd": self.RD_DEFAULT,
                                          "vol": self.VOL_DEFAULT}
            
        with open(filepath, 'w') as f:
            json.dump(ratings_data, f, indent=4)
            
    def init_unranked_into_ranked(self):
        """Adds rankstring into filename and moves un-initialised
        files into the ranked folder"""

        for filename in os.listdir(self.unranked_fol):
            new_filename = self.filename_mgr.add_rankstring_to_filename(filename, self.RATING_DEFAULT)
            os.rename(f'{self.unranked_fol}/{filename}',
                      f'{self.ranked_fol}/{new_filename}')
            
    def _read_ranked_folder(self):
        self.ranked_filenames = os.listdir(self.ranked_fol)
        self.num_ranked_resumes = len(self.ranked_filenames)
        self.ranked_filenames.sort()
    
    def unrank_files(self, idx_low=None, idx_high=None):
        """Move ranked files with index in `range(idx_low, idx_high)` back into the unranked folder."""
        self._read_ranked_folder()
        if self.num_ranked_resumes == 0:
            print("ranked folder empty")
            return

        # Clean up input
        if idx_low == None:
            idx_low = 0
        if idx_high == None:
            idx_high = self.num_ranked_resumes

        if idx_low not in range(self.num_ranked_resumes):
            raise ValueError('bad low index')
        if idx_high not in range(1, self.num_ranked_resumes+1):
            raise ValueError('bad high index')
        
        # Read JSON
        filepath = f'{self.resume_fol}/ratings.json'
        with open(filepath, 'r') as f:
            ratings_data = json.load(f)

        # Move the files and delete from ratings_data dict
        for i in range(idx_low, idx_high):
            # Move files
            filename = self.ranked_filenames[i]
            new_filename = self.filename_mgr.rm_rankstring_from_filename(filename)
            os.rename(f'./{self.ranked_fol}/{filename}',
                      f'./{self.unranked_fol}/{new_filename}')      
            # Delete data
            ratings_data.pop(new_filename)
            print(f'Unranked {filename}')

        # Write JSON
        with open(filepath, 'w') as f:
            json.dump(ratings_data, f, indent=4)

if __name__ == "__main__":
    mgr = ResumeManager('resumes_uk_copy')
    mgr.init_unranked()
    #mgr.unrank_files()

