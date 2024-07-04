class RankString:
    """
    A bunch of useful functions for dealing with the rank-based
    naming convention of the files.
    """

    def string_from_rank(self, rank):
        rankstring = str(rank)
        len_string = 3

        return "0" * (len_string - len(rankstring)) + rankstring
    
    def decrement_rankstring(self, rankstring, by=1):
        rank = int(rankstring)
        rank -= by
        return self.string_from_rank(rank)

    def increment_rankstring(self, rankstring, by=1):
        rank = int(rankstring)
        rank += by
        return self.string_from_rank(rank)
    
    @staticmethod
    def extract_rankstring(filename):
        split = filename.split('-')
        return split[0], ''.join(split[1:])
    
    def increment_ranked_filename(self, filename, by=1):
        rankstring, og_filename = self.extract_rankstring(filename)
        rankstring = self.increment_rankstring(rankstring, by=by)

        return f'{rankstring}-{og_filename}'
    
    def decrement_ranked_filename(self, filename, by=1):
        return self.increment_ranked_filename(filename, by=-by)
    
    def add_rankstring_to_filename(self, filename, rank):
        return f'{self.string_from_rank(rank)}-{filename}'
    
    def rm_rankstring_from_filename(self, filename):
        """012-my_bad_cv.png -> my_bad_cv.png"""
        return self.extract_rankstring(filename)[1]