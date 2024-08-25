import os
import json
import imghdr
from filename_manager import FilenameManager
from resume_rating_manager import RatingManager

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

        self.ratings_mgr = RatingManager(resume_folder, self.ranked_filenames)
        self.filename_mgr = FilenameManager()

    def update_ratings(self, num_matches=None):
        """Get new match data, then update ratings.json and filenames."""
        with open(f'{self.resume_fol}/ratings.json', 'r') as f:
            ratings_data = json.load(f)

        # Play matches
        new_ratings_data, comparisons = self.ratings_mgr.update_ratings(ratings_data, num_matches)

        # Update ratings JSON
        with open(f'{self.resume_fol}/ratings.json', 'w') as f:
            json.dump(new_ratings_data, f, indent=4)

        # Update comparisons JSON
        with open(f'{self.resume_fol}/comparisons.json', 'r') as f:
            comparisons_json = json.load(f)
            comparisons_json += comparisons
        
        with open(f'{self.resume_fol}/comparisons.json', 'w') as f:
            json.dump(comparisons_json, f, indent=4)

        # Update filenames
        for resume in self.ranked_filenames:
            old_rating, filename = self.filename_mgr.get_rankstring(resume)
            new_rating = new_ratings_data[filename]['rating']
            new_rating = int(new_rating)
            os.rename(f'{self.ranked_fol}/{old_rating}-{filename}',
                      f'{self.ranked_fol}/{new_rating}-{filename}')

    @staticmethod
    def _correct_filetype(file_path, filename):
        """Corrects filenames with '.png' that are actually jpeg (and vice versa)"""
        file_type_claimed = filename[-3:]
        file_type_actual = imghdr.what(file_path)
        if file_type_claimed == 'png' and file_type_actual == 'jpeg':
            return filename[:-3] + 'jpg'
        elif file_type_claimed == 'jpg' and file_type_actual == 'png':
            return filename[:-3] + 'png'

        return filename

    def correct_filetypes(self, resume_folder=None):
        """fix a resume folder's incorrect filetypes"""
        if not resume_folder:
            resume_folder = self.ranked_fol

        for filename in os.listdir(resume_folder):
            corrected_filename = self._correct_filetype(f'{resume_folder}/{filename}', filename)
            if filename != corrected_filename:
                print(f'corrected {filename} to {corrected_filename}')
                os.rename(f'{resume_folder}/{filename}',
                          f'{resume_folder}/{corrected_filename}')
    
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
            file_path = f'{self.unranked_fol}/{filename}'

            # Claude only supports images of size < 5mb
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            if file_size > 5:
                print(f'Resume "{filename}" is too large, skipping...')
                continue

            # Change '.jpg' to '.png' if needed
            new_filename = self._correct_filetype(file_path, filename)

            if new_filename in ratings_data:
                print(f'Resume "{filename}" is already initialised in ratings.json')
                print("Skipping...")
                continue

            # Add data to json
            ratings_data[new_filename] = {"rating": self.RATING_DEFAULT,
                                          "rd": self.RD_DEFAULT,
                                          "vol": self.VOL_DEFAULT}
            
            # Move file
            new_filename = self.filename_mgr.add_rankstring_to_filename(new_filename, self.RATING_DEFAULT)
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
            if new_filename in ratings_data:
                ratings_data.pop(new_filename)
            print(f'Unranked {filename}')

        # Write JSON
        with open(filepath, 'w') as f:
            json.dump(ratings_data, f, indent=4)

if __name__ == "__main__":
    mgr = ResumeManager('resumes_uk')

    # mgr.unrank_files(9, 24)
    
    # mgr.init_unranked()
    mgr.update_ratings(num_matches=200)

    # import imghdr
    # file_path = 'resumes_uk/ranked'
    # for resume in os.listdir(file_path):
    #     image_type = imghdr.what(f'{file_path}/{resume}')
    #     print(f'filename={resume}, {image_type=}')

    
"""
BACKLOG

- check file size is less than 5mb when initialising
- check filetype is correct when initialising
"""