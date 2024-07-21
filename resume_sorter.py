from resume_comparer import LLMResumeComparer
from rankstring import RankString
import os
import json

class ResumeSorter:
    """
    Repeatedly makes calls to LLMResumeComparer, using insertion sort
    to rank resumes in the 'unranked' folder.

    Parameters:
    - resume_folder (str): name of the folder that contains 'ranked', 'unranked' and 'storage' folders.
    """
    def __init__(self, resume_folder, debug=False):
        self.resume_comparer = LLMResumeComparer(resume_folder)
        self.resume_folder = resume_folder
        self.debug = debug

        # Store comparisons
        self.comparisons = []

        self.rank_string = RankString()

    def find_rank(self):
        """
        Algorithm:
        1. Sonnet (best of 3) to determine initial direction of resume
        2. Keep using Haiku (best of 1) until direction seems to change
        3. Confirm direction change with Sonnet (best of 1)
        """

        # Initial rank is median
        self.current_rank = (self.num_ranked_resumes - 1) // 2
        
        first_comparison_is_win = None            

        done = False
        while not done:
            print(f'{self.current_rank=}')

            # Determine initial direction
            if first_comparison_is_win == None:
                comparison = self._bon_with_ranked_at_curr(self.current_rank, n=3)

                # There might have been a filetype error; change .jpg to .png (or vice versa)
                if self.resume_comparer.should_swap_mediatype:
                    old_directory = f'./{self.resume_folder}/unranked/{self.to_be_ranked_filename}'
                    mediatype = self.to_be_ranked_filename[-3:]
                    filename = self.to_be_ranked_filename[:-3]
                    mediatype = 'png' if mediatype == 'jpg' else 'jpg'

                    self.to_be_ranked_filename = filename + mediatype
                    new_directory = f'./{self.resume_folder}/unranked/{self.to_be_ranked_filename}'

                    os.rename(old_directory, new_directory)
                    
                first_comparison_is_win = self._is_winner_to_be_ranked(comparison)
                print('first: win' if first_comparison_is_win else 'first: loss')
                # Increment or decrement rank
                done = self._incr_rank(first_comparison_is_win)
                continue

            # Make comparison between two resumes
            comparison = {'winner': None}
            while comparison['winner'] == None:
                comparison = self._compare_with_ranked_at_curr(self.current_rank)

            comparison_is_win = self._is_winner_to_be_ranked(comparison)
            print('win' if comparison_is_win else 'loss')

            # If direction seems to change, do best of 3 to confirm
            if first_comparison_is_win != comparison_is_win:
                comparison = self._bon_with_ranked_at_curr(self.current_rank, n=1)
                comparison_is_win = self._is_winner_to_be_ranked(comparison)
                # If confirmed comparison did in fact change, end loop
                if comparison_is_win != first_comparison_is_win:
                    if not comparison_is_win:
                        self._incr_rank(comparison_is_win)
                    break
                # Otherwise continue

            # Increment or decrement rank            
            done = self._incr_rank(first_comparison_is_win)

        print(f'final rank = {self.current_rank}')
        return self.current_rank # todo: change so that this is just accessed not returned
    
    def _incr_rank(self, comparison_is_win):
        """
        Increments / decrements `self.current_rank` based on whether the resume won.
        Returns `True` or `False` meaning "are we done incrementing".
        """
        self.current_rank += -1 if comparison_is_win else +1
        if self.current_rank == -1:
            self.current_rank = 0
            return True
        if self.current_rank == self.num_ranked_resumes:
            return True
        
        return False

    def _bon_with_ranked_at_curr(self, current_rank, n=3):
        """Best of n comparison with ranked resume at rank `current_rank`"""
        ranked_resume_at_curr = self.ranked_filenames[current_rank]
        print(f'COMPARISON: {self.to_be_ranked_filename} vs {ranked_resume_at_curr}')
        self.resume_comparer.model = 'sonnet'
        print('model=sonnet')
        comparison = self.resume_comparer.best_of_n(n, self.to_be_ranked_filename, ranked_resume_at_curr)
        if self.debug:
            input('Best of n complete. Continue?')
        return comparison

    def _compare_with_ranked_at_curr(self, current_rank):
        """Compare resume with ranked resume at rank `current_rank`"""
        ranked_resume_at_curr = self.ranked_filenames[current_rank]
        print(f'COMPARISON: {self.to_be_ranked_filename} vs {ranked_resume_at_curr}')
        self.resume_comparer.model = 'haiku'
        print('model=haiku')
        comparison = self.resume_comparer.main(self.to_be_ranked_filename, ranked_resume_at_curr)
        self.resume_comparer.pretty_print(comparison)
        if self.debug:
            input('Continue?')
        return comparison
    
    @staticmethod
    def _is_winner_to_be_ranked(comparison):
        return comparison['winner'] == comparison['to_be_ranked_resume']
    
    def insert_unranked_file(self, rank):
        """Move unranked file into ranked folder based on its final rank."""

        # Derank everything with rank >= `rank`
        for filename in self.ranked_filenames[rank:]:
            os.rename(f'./{self.resume_folder}/ranked/{filename}', f'./{self.resume_folder}/ranked/{self.rank_string.increment_ranked_filename(filename)}')

        # Add the rank to the to-be-ranked filename
        new_filename = self.rank_string.add_rankstring_to_filename(self.to_be_ranked_filename, rank)

        # Move from unranked folder to ranked folder
        os.rename(f'./{self.resume_folder}/unranked/{self.to_be_ranked_filename}', f'./{self.resume_folder}/ranked/{new_filename}')

    def unrank_files(self, idx_low=None, idx_high=None):
        """Move ranked files with index in `range(idx_low, idx_high)` back into the unranked folder."""
        self.read_ranked_folder()
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
        
        # Move the files
        for i in range(idx_low, idx_high):
            filename = self.ranked_filenames[i]
            new_filename = self.rank_string.rm_rankstring_from_filename(filename)
            os.rename(f'./{self.resume_folder}/ranked/{filename}', f'./{self.resume_folder}/unranked/{new_filename}')
            print(f'Unranked {filename}')

        # Update the rank of the remaining files
        # Suppose idx_low, idx_high = 1, 4
        # 001-003 inclusive is removed
        # everything >= idx_low must have rank decremented by (idx_high - idx_low)
        self.read_ranked_folder()
        for i in range(idx_low, self.num_ranked_resumes):
            filename = self.ranked_filenames[i]
            new_filename = self.rank_string.decrement_ranked_filename(filename, by = idx_high - idx_low)
            os.rename(f'./{self.resume_folder}/ranked/{filename}', f'./{self.resume_folder}/ranked/{new_filename}')
    
    def read_ranked_folder(self):
        self.num_ranked_resumes = len(os.listdir(f'./{self.resume_folder}/ranked'))
        self.ranked_filenames = os.listdir(f'./{self.resume_folder}/ranked')
        self.ranked_filenames.sort()

    def insert(self, to_be_ranked_filename):
        # Re-read ranked folder
        self.read_ranked_folder()

        # If ranked folder empty, initialise
        if self.num_ranked_resumes == 0:
            new_filename = self.rank_string.add_rankstring_to_filename(to_be_ranked_filename, rank=0)
            os.rename(f'./{self.resume_folder}/unranked/{to_be_ranked_filename}', f'./{self.resume_folder}/ranked/{new_filename}')
            return

        # Insert
        print(f'Ranking: {to_be_ranked_filename}')
        self.to_be_ranked_filename = to_be_ranked_filename
        rank = self.find_rank()
        self.insert_unranked_file(rank)

    def _update_usage_json(self, num_calls):
        """
        usage.json stores how many times each model was called.
        This function updates the json at the end of `insert_all()`.
        """
        filepath = f'{self.resume_folder}/usage.json'

        with open(filepath, 'r') as file:
            usage_data = json.load(file)

        for key, value in num_calls.items():
            if key in usage_data['num_calls']:
                usage_data['num_calls'][key] += value
            else:
                usage_data['num_calls'][key] = value

        with open(filepath, 'w') as file:
            json.dump(usage_data, file, indent=4)

    def insert_all(self):
        for filename in os.listdir(f'./{self.resume_folder}/unranked'):  
            self.insert(filename)
            if self.debug:
                self.read_ranked_folder()
                print(f'ranked_files={self.ranked_filenames}')
        
        num_calls = self.resume_comparer.num_calls
        print(f'num_calls={num_calls}')
        self._update_usage_json(num_calls)

if __name__ == '__main__':
    RESUME_FOLDER = 'resumes_uk copy'

    sorter = ResumeSorter(RESUME_FOLDER)
    sorter.unrank_files()
    # sorter.insert_all()

"""
BACKLOG

- Dynamic switching between haiku and sonnet
- JSON file that counts # of api calls
- Implement JSON support
- Reduce repeated code when making `os.` calls
- Ability to create folders
"""

"""
Current goal: correctly implement `find_rank()` DONE
- 

"""