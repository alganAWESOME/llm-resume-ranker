from resume_comparer import LLMResumeComparer
from rankstring import RankString
import os

class ResumeSorter:
    def __init__(self):
        self.resume_comparer = LLMResumeComparer()

        # Store comparisons
        self.comparisons = []

        self.rank_string = RankString()

    def find_rank(self):
        """
        Start by comparing resume with median ranked resume.

        Keep moving resume in that direction until the opposite happens twice,
        e.g. if it wins at median, keep ranking it better and better
        until it loses twice to a resume.
        """
        # Initial rank is median
        current_rank = (self.num_ranked_resumes - 1) // 2
        
        first_comparison_is_win = None

        opposite_results = 0
        while opposite_results < 1:
            print(f'{current_rank=}')

            # Make comparison between two resumes
            comparison = {'winner': None}
            while comparison['winner'] == None:
                comparison = self._compare_with_ranked_at_curr(current_rank)

            comparison_is_win = self._is_winner_to_be_ranked(comparison)
            print('to-be-ranked won' if comparison_is_win else 'to-be-ranked lost')

            # Determine initial direction
            if first_comparison_is_win == None:
                first_comparison_is_win = comparison_is_win

            if first_comparison_is_win != comparison_is_win:
                opposite_results += 1
            else:
                current_rank += -1 if first_comparison_is_win else +1
                if current_rank == 0 or current_rank == self.num_ranked_resumes - 1:
                    break

        print(f'final rank = {current_rank}')
        return current_rank

    def _compare_with_ranked_at_curr(self, current_rank):
        """Compare resume with ranked resume at rank `current_rank`"""
        ranked_resume_at_curr = self.ranked_filenames[current_rank]
        comparison = self.resume_comparer.main(self.to_be_ranked_filename, ranked_resume_at_curr)
        return comparison
    
    @staticmethod
    def _is_winner_to_be_ranked(comparison):
        return comparison['winner'] == comparison['to_be_ranked_resume']
    
    def insert_unranked_file(self, rank):
        """Move unranked file into ranked folder based on its final rank."""

        # Derank everything with rank >= `rank`
        for filename in self.ranked_filenames[rank:]:
            os.rename(f'./ranked/{filename}', f'./ranked/{self.rank_string.increment_ranked_filename(filename)}')

        # Add the rank to the to-be-ranked filename
        new_filename = self.rank_string.add_rankstring_to_filename(self.to_be_ranked_filename, rank)

        # Move from unranked folder to ranked folder
        os.rename(f'./unranked/{self.to_be_ranked_filename}', f'./ranked/{new_filename}')

        print(f'mv ./unranked/{self.to_be_ranked_filename} ./ranked/{new_filename}')

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
            os.rename(f'./ranked/{filename}', f'./unranked/{new_filename}')
            print(f'Unranked {filename}')

        # Update the rank of the remaining files
        # Suppose idx_low, idx_high = 1, 4
        # 001-003 inclusive is removed
        # everything >= idx_low must have rank decremented by (idx_high - idx_low)
        self.read_ranked_folder()
        for i in range(idx_low, self.num_ranked_resumes):
            filename = self.ranked_filenames[i]
            new_filename = self.rank_string.decrement_ranked_filename(filename, by = idx_high - idx_low)
            os.rename(f'./ranked/{filename}', f'./ranked/{new_filename}')
    
    def read_ranked_folder(self):
        self.num_ranked_resumes = len(os.listdir('./ranked'))
        self.ranked_filenames = os.listdir('./ranked')
        self.ranked_filenames.sort()

    def insert(self, to_be_ranked_filename):
        # Re-read ranked folder
        self.read_ranked_folder()

        # If ranked folder empty, initialise
        if self.num_ranked_resumes == 0:
            new_filename = self.rank_string.add_rankstring_to_filename(to_be_ranked_filename, rank=0)
            os.rename(f'./unranked/{to_be_ranked_filename}', f'./ranked/{new_filename}')
            return

        # Insert
        print(f'Ranking: {to_be_ranked_filename}')
        self.to_be_ranked_filename = to_be_ranked_filename
        rank = self.find_rank()
        self.insert_unranked_file(rank)

    def insert_all(self):
        for filename in os.listdir('./unranked'):
            self.insert(filename)

if __name__ == '__main__':
    sorter = ResumeSorter()
    # sorter.insert_all()
    sorter.unrank_files()
    sorter.insert_all()

"""
TODO
- Best of n at the start and end of comparisons
- implement JSON support
- Function which compares everything in unranked (easy) DONE

longterm: evaluation strategy?
"""