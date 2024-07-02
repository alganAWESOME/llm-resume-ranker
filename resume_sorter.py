from resume_comparer import LLMResumeComparer
from rankstring import RankString
import os

class ResumeSorter:
    def __init__(self):
        self.resume_comparer = LLMResumeComparer()

        self.num_ranked_resumes = len(os.listdir('./ranked'))
        self.ranked_filenames = os.listdir('./ranked')
        self.ranked_filenames.sort()

        # Store comparisons
        self.comparisons = []

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
            comparison = self._compare_with_ranked_at_curr(current_rank)
            comparison_is_win = self._is_winner_to_be_ranked(comparison)
            if first_comparison_is_win == None:
                first_comparison_is_win = comparison_is_win

            if first_comparison_is_win != comparison_is_win:
                opposite_results += 1
            else:
                current_rank += -1 if first_comparison_is_win else +1
                print(f'current rank after increment is {current_rank}')
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
        rank_string = RankString()

        # Derank everything with rank >= `rank`
        for filename in self.ranked_filenames[rank:]:
            os.rename(f'./ranked/{filename}', f'./ranked/{rank_string.derank_filename(filename)}')

        # Add the rank to the to-be-ranked filename
        new_filename = rank_string.add_rankstring_to_filename(self.to_be_ranked_filename, rank)

        os.rename(f'./unranked/{self.to_be_ranked_filename}', f'./ranked/{new_filename}')

        print(f'mv ./unranked/{self.to_be_ranked_filename} ./ranked/{new_filename}')

    def insert(self, to_be_ranked_filename):
        print(f'Ranking: {to_be_ranked_filename}')
        self.to_be_ranked_filename = to_be_ranked_filename
        rank = self.find_rank()
        self.insert_unranked_file(rank)

if __name__ == '__main__':
    sorter = ResumeSorter()
    filename = 'aaaresume2.png'
    sorter.insert(filename)