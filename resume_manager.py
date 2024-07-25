import os
import json
from filename_manager import FilenameManager
from resume_ratings_manager import RatingManager

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

        self._read_ranked_folder()

        self.ratings_mgr = RatingManager(self.ranked_filenames)
        self.filename_mgr = FilenameManager()

    def update_ratings(self, num_matches=None):
        """Get new match data, then update ratings.json and filenames."""
        with open(f'{self.resume_fol}/ratings.json', 'r') as f:
            ratings_data = json.load(f)

        # Play matches
        new_ratings_data = self.ratings_mgr.update_ratings(ratings_data, num_matches)

        # Update JSON
        with open(f'{self.resume_fol}/ratings.json', 'w') as f:
            json.dump(new_ratings_data, f, indent=4)

        # Update filenames
        for resume in self.ranked_filenames:
            old_rating, filename = self.filename_mgr.get_rankstring(resume)
            new_rating = new_ratings_data[filename]['rating']
            new_rating = int(new_rating)
            os.rename(f'{self.ranked_fol}/{old_rating}-{filename}',
                      f'{self.ranked_fol}/{new_rating}-{filename}')

    def init_unranked(self):
        """
        Adds unranked resumes into `ratings.json`.
        Adds rankstring into filename and moves un-initialised
        files into the ranked folder.
        """

        filepath = f'{self.resume_fol}/ratings.json'
        with open(filepath, 'r') as f:
            ratings_data = json.load(f)

        for filename in os.listdir(self.unranked_fol):
            if filename in ratings_data:
                print(f'File named "{filename}" is already initialised in ratings.json')
                print("Skipping...")
                continue

            # Add data to json
            ratings_data[filename] = {"rating": self.RATING_DEFAULT,
                                          "rd": self.RD_DEFAULT,
                                          "vol": self.VOL_DEFAULT}
            
            # Move file
            new_filename = self.filename_mgr.add_rankstring_to_filename(filename, self.RATING_DEFAULT)
            os.rename(f'{self.unranked_fol}/{filename}',
                      f'{self.ranked_fol}/{new_filename}')
            
        with open(filepath, 'w') as f:
            json.dump(ratings_data, f, indent=4)
            
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
            new_filename = self.filename_mgr.rm_rankstring(filename)
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
    # mgr.unrank_files()
    # mgr.init_unranked()
    mgr.update_ratings()
    #mgr.unrank_files()
